# coding:utf-8
# @文件: views_user.py
# @创建者：州的先生
# #日期：2020/11/7
# 博客地址：zmister.com
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
from app_admin.models import UserOptions, SysSetting, Plant
from app_doc.models import DocBottomConfiguration


# 个人中心
from app_doc.spider.cnblog_publish import CNBlogPublish
from app_doc.spider.csdn_publish import CSDNPublish
from app_doc.spider.segfault_publish import SegFaultPublish
from app_doc.spider.zhihu_publish import ZhiHuPublish


# 替换前端传来的非法字符
def validateTitle(title):
  rstr = r"[\/\\\:\*\?\"\<\>\|\[\]]" # '/ \ : * ? " < > |'
  new_title = re.sub(rstr, "_", title) # 替换为下划线
  return new_title


@login_required()
def user_center(request):
    return render(request,'app_doc/user/user_center.html',locals())


# 后台管理 - 发布平台cookie管理
@login_required()
@logger.catch(reraise=True)
def cookie_manage(request):
    # 发布平台cookie管理页面
    if request.method == 'GET':
        plant_list = Plant.objects.all()
        register_codes = CookiePlant.objects.filter(create_user=request.user)
        # print(register_codes)
        paginator = Paginator(register_codes, 10)
        page = request.GET.get('page', 1)
        try:
            codes = paginator.page(page)
        except PageNotAnInteger:
            codes = paginator.page(1)
        except EmptyPage:
            codes = paginator.page(paginator.num_pages)
        return render(request, 'app_doc/user/user_cookie_manage.html', locals())
    elif request.method == 'POST':
        types = request.POST.get('types', None)
        if types is None:
            return JsonResponse({'status': False, 'data': '参数错误'})
        # types表示操作的类型，1表示新增、2表示修改
        if int(types) == 1:
            try:
                plant_cookie = request.POST.get('plant_cookie')  # cookie
                plant_id = request.POST.get('plant_id')  # 平台id
                plant = Plant.objects.filter(id=int(plant_id), status=1)
                if plant:
                    is_true = CookiePlant.objects.filter(plant=plant[0], create_user=request.user)
                    if is_true:
                        return JsonResponse({'status': False, 'data': '新增失败！当前不支持同平台多账号！'})
                    # 创建一个 cookie
                    CookiePlant.objects.create(
                        cookie=plant_cookie,
                        plant=plant[0],
                        status=1,
                        create_user=request.user
                    )
                    return JsonResponse({'status': True, 'data': '新增成功'})
                else:
                    return JsonResponse({'status': False, 'data': '新增失败！当前平台不可用！'})
            except Exception as e:
                logger.exception("新增发布平台异常")
                return JsonResponse({'status': False, 'data': '系统异常'})
        elif int(types) == 2:  # 更新 cookie
            code_id = request.POST.get('code_id', None)
            cookie = request.POST.get('cookie')
            try:

                CookiePlant.objects.filter(id=int(code_id)).update(status=1, cookie=cookie)
                # print(register_code)
                return JsonResponse({'status': True, 'data': '操作成功'})
            except ObjectDoesNotExist:
                return JsonResponse({'status': False, 'data': '当前平台不存在'})
            except:
                print(traceback.format_exc())
                return JsonResponse({'status': False, 'data': '系统异常'})
        else:
            return JsonResponse({'status': False, 'data': '类型错误'})
    else:
        return JsonResponse({'status': False, 'data': '方法错误'})


# 文章分发
@login_required()
@require_POST
@logger.catch(reraise=True)
def article_distribution(request):
    # 发布文章
    code_id = request.POST.get('code_id', None)
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
            return JsonResponse({'status': False, 'data': '当前文章没有发布哦！'})
        cookie = CookiePlant.objects.filter(id=int(code_id), create_user=request.user)
        cookie_user = cookie[0].create_user
        plant_cookie = cookie[0].cookie
        plant_name = cookie[0].plant.plant_name
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
        if doc_plant_list and plant_name in doc_plant_list:
            return JsonResponse({'status': False, 'data': f'当前文章在 {plant_name} 平台已发布'})
        if doc_create_user == cookie_user and cookie_user == request.user:
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
                # print(register_code)
                return JsonResponse({'status': True, 'data': '发布成功'})
            return JsonResponse({'status': False, 'data': '发布失败'})
        else:
            return JsonResponse({'status': False, 'data': '该文章不是你的哦！'})
    except ObjectDoesNotExist:
        return JsonResponse({'status': False, 'data': '当前平台不存在'})
    except:
        print(traceback.format_exc())
        return JsonResponse({'status': False, 'data': '系统异常'})


# 文章底部模板管理
@login_required()
@logger.catch(reraise=True)
def bottom_template_manage(request):
    try:
        if request.method == 'GET':
            return render(request, 'app_doc/user/user_bottom_manage.html', locals())
        if request.method == 'POST':
            project_list = DocBottomConfiguration.objects.filter(create_user=request.user).order_by('-create_time')
            table_data = []
            for project in project_list:
                item = {
                    'id': project.id,
                    'name': project.name,
                    'content': project.content,
                    'is_default': project.is_default,
                    'create_user': project.create_user.username,
                    'create_time': project.create_time,
                    'modify_time': project.modify_time
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


# 后台管理 - 控制文集置顶状态
@login_required()
@require_POST
def bottom_is_default(request):
    try:
        bottom_id = request.POST.get('id')
        is_default = request.POST.get('is_default')
        if is_default == 'true':
            is_default = True
        else:
            is_default = False
        if is_default:
            other_default = False
            DocBottomConfiguration.objects.exclude(id=bottom_id).update(is_default=other_default)
        DocBottomConfiguration.objects.filter(id=bottom_id).update(is_default=is_default)
        return JsonResponse({'status': True})
    except:
        logger.exception("设置默认出错")
        return JsonResponse({'status': False, 'data': '执行出错'})


# 创建底部模板
@login_required()
@require_POST
def create_bottom_template(request):
    try:
        name = request.POST.get('pname','')
        name = validateTitle(name)
        desc = request.POST.get('desc','')
        if name != '':
            bottom = DocBottomConfiguration.objects.create(
                name=validateTitle(name),
                content=desc[:500],
                is_default=0,
                create_user=request.user,
            )
            bottom.save()
            return JsonResponse({'status':True,'data':{'id':bottom.id,'name':bottom.name}})
        else:
            return JsonResponse({'status':False,'data':'模板名不能为空！'})
    except Exception as e:
        logger.exception("创建文章底部模板出错")
        return JsonResponse({'status':False,'data':'出现异常,请检查输入值！'})


# 删除底部模板
@login_required()
@require_POST
def del_bottom(request):
    try:
        bottom_id = request.POST.get('bottom_id','')
        range = request.POST.get('range', 'single')
        if bottom_id != '':
            if range == 'single':
                pro = DocBottomConfiguration.objects.get(id=bottom_id)
                if request.user == pro.create_user:
                    # 删除文集
                    pro.delete()
                    return JsonResponse({'status':True})
                else:
                    return JsonResponse({'status':False,'data':'非法请求'})
        elif range == 'multi':
            pros = bottom_id.split(",")
            try:
                projects = DocBottomConfiguration.objects.filter(id__in=pros, create_user=request.user)
                projects.delete()
                return JsonResponse({'status': True, 'data': 'ok'})
            except Exception:
                logger.exception("异常")
                return JsonResponse({'status': False, 'data': '无指定内容'})
        else:
            return JsonResponse({'status':False,'data':'参数错误'})
    except Exception as e:
        logger.exception("删除出错")
        return JsonResponse({'status':False,'data':'请求出错'})


# 个人中心菜单
def user_center_menu(request):
    menu_data = [
        {
            "id": 1,
            "title": "仪表盘",
            "type": 1,
            "icon": "layui-icon layui-icon-console",
            "href": reverse('manage_overview'),
        },
        {
            "id": "my_project",
            "title": "我的文集",
            "icon": "layui-icon layui-icon-component",
            "type": 0,
            "href": "",
            "children": [
                {
                    "id": "manage_project",
                    "title": "文集管理",
                    "icon": "layui-icon layui-icon-console",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse('manage_project')
                },
                {
                    "id": "manage_colla_self",
                    "title": "我的协作",
                    "icon": "layui-icon layui-icon-console",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse('manage_pro_colla_self')
                },
                {
                    "id": "import_project",
                    "title": "导入文集",
                    "icon": "layui-icon layui-icon-console",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse('import_project')
                },
            ]
        },
        {
            "id": "my_doc",
            "title": "我的文档",
            "icon": "layui-icon layui-icon-file-b",
            "type": 0,
            "href": "",
            "children": [
                {
                    "id": "doc_manage",
                    "title": "文档管理",
                    "icon": "layui-icon layui-icon-face-smile",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("manage_doc")
                },
                {
                    "id": "doc_publish_manage",
                    "title": "分发数据管理",
                    "icon": "layui-icon layui-icon-face-smile",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("doc_publish_manage")
                },
                {
                    "id": "doc_cookie_manage",
                    "title": "cookie 管理",
                    "icon": "layui-icon layui-icon-face-smile",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("cookie_manage")
                },
                {
                    "id": "bottom_template_manage",
                    "title": "底部模板",
                    "icon": "layui-icon layui-icon-face-smile",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("bottom_template_manage")
                },
                {
                    "id": "drawing_bed_setting",
                    "title": "图床配置",
                    "icon": "layui-icon layui-icon-face-smile",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("drawing_bed_setting")
                },
                {
                    "id": "doc_template",
                    "title": "文档模板",
                    "icon": "layui-icon layui-icon-face-cry",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("manage_doctemp")
                },
                {
                    "id": "doc_tag",
                    "title": "文档标签",
                    "icon": "layui-icon layui-icon-face-cry",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("manage_doc_tag")
                },
                {
                    "id": "doc_share",
                    "title": "我的分享",
                    "icon": "layui-icon layui-icon-face-cry",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("manage_doc_share")
                },
                {
                    "id": "doc_recycle",
                    "title": "文档回收站",
                    "icon": "layui-icon layui-icon-face-cry",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("doc_recycle")
                }
            ]
        },
        {
            "id": "my_fodder",
            "title": "我的素材",
            "icon": "layui-icon layui-icon-upload-drag",
            "type": 0,
            "href": "",
            "children": [
                {
                    "id": "my_img",
                    "title": "我的图片",
                    "icon": "layui-icon layui-icon-face-smile",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("manage_image")
                },
                {
                    "id": "my_attachment",
                    "title": "我的附件",
                    "icon": "layui-icon layui-icon-face-cry",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("manage_attachment")
                },
            ]
        },
        {
            "id": "my_collect",
            "title": "我的收藏",
            "icon": "layui-icon layui-icon-star",
            "type": 1,
            "openType": "_iframe",
            "href": reverse("manage_collect")
        },
        {
            "id": "self_settings",
            "title": "个人管理",
            "icon": "layui-icon layui-icon-set-fill",
            "type": 0,
            "href": "",
            "children": [
                {
                    "id": 601,
                    "title": "个人设置",
                    "icon": "layui-icon layui-icon-face-smile",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("manage_self")
                },
                {
                    "id": 602,
                    "title": "Token管理",
                    "icon": "layui-icon layui-icon-face-cry",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("manage_token")
                },
            ]
        },
        {
            "id": "user_manual",
            "title": "使用手册",
            "icon": "layui-icon layui-icon-template-1",
            "type": 1,
            "openType": "_blank",
            "href": "http://mrdoc.zmister.com/project-54/",
        }
        # {
        #     "id": "common",
        #     "title": "使用帮助",
        #     "icon": "layui-icon layui-icon-template-1",
        #     "type": 0,
        #     "href": "",
        #     "children": [{
        #         "id": 701,
        #         "title": "安装说明",
        #         "icon": "layui-icon layui-icon-face-smile",
        #         "type": 1,
        #         "openType": "_iframe",
        #         "href": "http://mrdoc.zmister.com/project-7/"
        #     }, {
        #         "id": 702,
        #         "title": "使用说明",
        #         "icon": "layui-icon layui-icon-face-smile",
        #         "type": 1,
        #         "openType": "_iframe",
        #         "href": "http://mrdoc.zmister.com/project-54/"
        #     }]
        # }
    ]
    return JsonResponse(menu_data,safe=False)
