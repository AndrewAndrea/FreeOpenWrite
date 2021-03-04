# coding:utf-8
# @文件: views_doc_pub.py
# @创建者：Andrew
# #日期：2021/02/26
# 博客地址：www.andrewblog.cn
import markdown
import json
from django.shortcuts import render,redirect
from django.http.response import JsonResponse
from django.contrib.auth.decorators import login_required # 登录需求装饰器
from django.core.paginator import Paginator,PageNotAnInteger,EmptyPage,InvalidPage # 后端分页
from django.core.exceptions import PermissionDenied,ObjectDoesNotExist
from django.db.models import Q
from django.urls import reverse
from django.views.decorators.http import require_POST
from loguru import logger
from app_doc.report_utils import *
from app_admin.models import UserOptions, SysSetting, Plant, CookiePlant
from app_doc.models import DocBottomConfiguration

from app_doc.spider.cnblog_publish import CNBlogPublish
from app_doc.spider.csdn_publish import CSDNPublish
from app_doc.spider.segfault_publish import SegFaultPublish
from app_doc.spider.zhihu_publish import ZhiHuPublish


# 文章分发记录管理
@login_required()
@logger.catch(reraise=True)
def doc_publish_manage(request):
    try:
        if request.method == 'GET':
            return render(request, 'app_doc/manage/manage_doc_publish.html', locals())
        if request.method == 'POST':
            project_list = DocPublishData.objects.filter(create_user=request.user).order_by('-create_time')
            table_data = []
            for project in project_list:
                item = {
                    'id': project.id,
                    'name': project.doc.name,
                    'doc_publish_url': project.doc_publish_url,
                    'plant_name': project.plant_name,
                    'status': project.status,
                    'read_num': project.read_num,
                    'star_num': project.star_num,
                    'comment_num': project.comment_num,
                    'create_time': project.create_time,
                }
                table_data.append(item)
            resp_data = {
                "code": 0,
                "msg": "ok",
                "count": project_list.count(),
                "data": table_data
            }
            return JsonResponse(resp_data)
    except:
        print(traceback.format_exc())


# 删除分发内容 ----- 直接删除所在平台已发布的内容
@login_required()
@require_POST
def del_doc_publish(request):
    try:
        doc_publish_id = request.POST.get('doc_publish_id', '')
        if doc_publish_id != '':
            pro = DocPublishData.objects.get(id=doc_publish_id)
            if request.user == pro.create_user:
                plant_name = pro.plant_name
                doc_publish_url = pro.doc_publish_url
                plant = Plant.objects.filter(plant_name=plant_name)
                cookies = CookiePlant.objects.get(plant=plant[0], create_user=request.user)
                if plant_name == "CSDN":
                    result = CSDNPublish(cookies).del_doc(doc_publish_url)
                elif plant_name == "博客园":
                    result = CNBlogPublish(cookies).del_doc(doc_publish_url)
                elif plant_name == "思否":
                    result = SegFaultPublish(cookies).del_doc(doc_publish_url)
                elif plant_name == "知乎":
                    result = ZhiHuPublish(cookies).del_doc(doc_publish_url)
                else:
                    return JsonResponse({'status': False, 'data': "非法请求"})
                if result:
                    Doc.objects.filter(id=pro.doc.id).update(plant_list=None)
                    pro.delete()
                    return JsonResponse({'status': True})

                return JsonResponse({'status':False, 'data': '删除失败！'})
            else:
                return JsonResponse({'status':False,'data':'非法请求'})
        else:
            return JsonResponse({'status':False,'data':'参数错误'})
    except Exception as e:
        logger.exception("删除出错")
        return JsonResponse({'status':False,'data':'请求出错'})


# 文章分发 ----- 一键分发到所有平台
@login_required()
@require_POST
@logger.catch(reraise=True)
def article_all_distribution(request):
    # 发布文章。获取所有平台的cookie，分发后返回分发结果
    doc_id = request.POST.get('doc_id', None)
    doc_tags = request.POST.get('tags', None)
    try:
        doc = Doc.objects.filter(id=int(doc_id), create_user=request.user)
        doc_create_user = doc[0].create_user
        doc_name = doc[0].name
        doc_pre_content = doc[0].pre_content
        # 已发布平台
        doc_plant_list = doc[0].plant_list
        editor_mode = doc[0].editor_mode
        doc_content = doc[0].content
        doc_status = doc[0].status
        if doc_status != 1:
            return JsonResponse({'status': False, 'data': '不能发布草稿哦！'})
        # 查询底部模板，如果有默认的模板，则自动拼接到文章结尾发布
        bottom = DocBottomConfiguration.objects.filter(is_default=True, create_user=request.user)
        if bottom.count():
            bottom_content = bottom[0].content
            md = markdown.Markdown(extensions=['markdown.extensions.extra', 'markdown.extensions.codehilite'])
            bottom_content_html = md.convert(bottom_content)
            doc_pre_content += '\n' + bottom_content
            doc_content += '\n' + bottom_content_html
        if editor_mode in [1, 2]:
            is_markdown = True
        else:
            doc_pre_content = doc_content
            is_markdown = False
        if doc_create_user != request.user:
            return JsonResponse({'status': False, 'data': '该文章不是你的哦！'})

        cookie = CookiePlant.objects.filter(create_user=request.user)

        all_result = {}

        for plant_info in cookie:
            cookie_user = plant_info.create_user
            plant_cookie = plant_info.cookie
            plant_name = plant_info.plant.plant_name
            all_result[plant_name] = {}
            if doc_plant_list and plant_name in doc_plant_list:
                all_result[plant_name] = {'status': False, 'data': f'当前文章在 {plant_name} 平台已发布'}
                continue

            if plant_name == 'CSDN':
                result = CSDNPublish(plant_cookie).publish_content(tags=doc_tags, title=doc_name,
                                                                   markdowncontent=doc_pre_content,
                                                                   content=doc_content)
                result_json = json.loads(result)
                code = result_json.get('code')
                msg = result_json.get('msg')
                publish_url = result_json.get('data').get('url')
                if code == 200 and msg == 'success' and publish_url:
                    pub_status = 1
                else:
                    pub_status = 0
            elif plant_name == '博客园':
                cnblog_ = CNBlogPublish(plant_cookie)
                result = cnblog_.publish_content(tags=doc_tags, title=doc_name,
                                                 markdowncontent=doc_pre_content, is_markdown=is_markdown)
                result_json = json.loads(result)
                publish_url = result_json.get('url')
                if publish_url:
                    publish_url = 'https:' + publish_url
                    pub_status = 1
                else:
                    pub_status = 0
            elif plant_name == '思否':
                seg_token = plant_cookie
                seg_pub = SegFaultPublish(seg_token=seg_token)
                result = seg_pub.publish_content(tags=doc_tags, markdowncontent=doc_pre_content, title=doc_name)
                if result == 'need_login':
                    cookie.update(status=0)
                    return JsonResponse({'status': False, 'data': '发布失败，请更换 cookie 后重新发布！'})
                r_json = json.loads(result)
                msg = r_json.get('msg')
                title = r_json.get('title')
                seg_data = r_json.get('data')
                if title:
                    return JsonResponse({'status': False, 'data': title})
                if seg_data:
                    article_id = seg_data.get('id')
                else:
                    return JsonResponse({'status': False, 'data': "发布失败！"})
                article_status = r_json.get('data').get('status')
                publish_url = 'https://segmentfault.com/a/' + str(article_id)
                pub_status = 1
            elif plant_name == '知乎':

                zhi_hu_pub = ZhiHuPublish(cookie=plant_cookie)
                result = zhi_hu_pub.publish_content(tags=doc_tags, title=doc_name, content=doc_content)

                r_json = json.loads(result)
                publish_url = r_json.get('url')
                title = r_json.get('title')
                seg_data = r_json.get('data')
                pub_status = 1
            else:
                result = None
                return JsonResponse({'status': False, 'data': '不支持当前平台！'})

            if result:
                DocPublishData.objects.create(
                    doc=doc[0],
                    plant_name=plant_name,
                    doc_publish_url=publish_url,
                    status=pub_status,
                    create_user=request.user
                )
                if doc_plant_list:
                    plant_list = doc_plant_list + ',' + plant_name
                else:
                    plant_list = plant_name
                doc.update(plant_list=plant_list)
            if pub_status == 1:
                all_result[plant_name] = {'status': True, 'data': f'在 {plant_name} 平台分发成功'}
            else:
                all_result[plant_name] = {'status': True, 'data': f'在 {plant_name} 平台分发失败'}
        return JsonResponse({'status': True, 'data': '发布已完成！', 'result': all_result})


    except ObjectDoesNotExist:
        return JsonResponse({'status': False, 'data': '当前平台不存在'})
    except:
        print(traceback.format_exc())
        return JsonResponse({'status': False, 'data': '系统异常'})


