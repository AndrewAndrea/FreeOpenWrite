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
from app_admin.models import Plant
from app_doc.models import DocBottomConfiguration

from app_doc.spider.cnblog_publish import CNBlogPublish
from app_doc.spider.csdn_publish import CSDNPublish
from app_doc.spider.segfault_publish import SegFaultPublish
from app_doc.spider.zhihu_publish import ZhiHuPublish
from app_doc.spider.juejin_publish import JueJinPublish


# 文章分发记录管理
@login_required()
@logger.catch(reraise=True)
def doc_publish_manage(request):
    try:
        if request.method == 'GET':
            # 渠道列表
            plant_list = Plant.objects.all()
            # 已发布文档数量
            published_doc_cnt = DocPublishData.objects.filter(create_user=request.user, status=1).count()
            # 发布失败文档数量
            draft_doc_cnt = DocPublishData.objects.filter(create_user=request.user, status=0).count()
            # 所有文档数量
            all_cnt = published_doc_cnt + draft_doc_cnt
            return render(request, 'app_doc/manage/manage_doc_publish.html', locals())
        if request.method == 'POST':
            kw = request.POST.get('kw', '')
            plant_name = request.POST.get('plant_name', '')
            status = request.POST.get('status', '')
            if status == '-1':  # 全部文档
                q_status = [0, 1]
            elif status in ['0', '1']:
                q_status = [int(status)]
            else:
                q_status = [0, 1]

            if plant_name == '':
                plant_name_list = DocPublishData.objects.filter(
                    create_user=request.user).values_list('plant_name', flat=True)  # 自己创建的文集列表                                                                                                       flat=True)  # 协作的文集列表
                q_plant_name_list = list(plant_name_list)
            else:
                q_plant_name_list = [plant_name]

            page = request.POST.get('page', 1)
            limit = request.POST.get('limit', 10)
            # 没有搜索
            if kw == '':
                doc_push_list = DocPublishData.objects.filter(
                    create_user=request.user,
                    status__in=q_status,
                    plant_name__in=q_plant_name_list
                ).order_by('-create_time')
            # 有搜索
            else:
                doc_push_list = DocPublishData.objects.filter(
                    Q(doc__name__icontains=kw) | Q(doc__content__icontains=kw),
                    create_user=request.user, status__in=q_status, plant_name__in=q_plant_name_list
                ).order_by('-create_time')
            # 渠道列表
            plant_list = Plant.objects.all()
            # 已发布文档数量
            published_doc_cnt = DocPublishData.objects.filter(create_user=request.user, status=1).count()
            # 发布失败文档数量
            draft_doc_cnt = DocPublishData.objects.filter(create_user=request.user, status=0).count()
            # 所有文档数量
            all_cnt = published_doc_cnt + draft_doc_cnt

            # 分页处理
            paginator = Paginator(doc_push_list, limit)
            page = request.GET.get('page', page)
            try:
                docs_push = paginator.page(page)
            except PageNotAnInteger:
                docs_push = paginator.page(1)
            except EmptyPage:
                docs_push = paginator.page(paginator.num_pages)

            # project_list = DocPublishData.objects.filter(create_user=request.user).order_by('-create_time')
            table_data = []
            for project in docs_push:
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
                "count": doc_push_list.count(),
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
        range = request.POST.get('range', 'single')
        if doc_publish_id != '':
            if range == 'single':
                pro = DocPublishData.objects.get(id=doc_publish_id)
                if request.user == pro.create_user:
                    plant_name = pro.plant_name
                    doc_publish_url = pro.doc_publish_url
                    plant = Plant.objects.filter(plant_name=plant_name)
                    cookies = CookiePlant.objects.get(plant=plant[0], create_user=request.user).cookie
                    if plant_name == "CSDN":
                        result = CSDNPublish(cookies).del_doc(doc_publish_url)
                    elif plant_name == "博客园":
                        result = CNBlogPublish(cookies).del_doc(doc_publish_url)
                    elif plant_name == "思否":
                        result = SegFaultPublish(cookies).del_doc(doc_publish_url)
                    elif plant_name == "知乎":
                        result = ZhiHuPublish(cookies).del_doc(doc_publish_url)
                    elif plant_name == "掘金":
                        result = JueJinPublish(cookies).del_doc(doc_publish_url)
                    else:
                        return JsonResponse({'status': False, 'data': "非法请求"})
                    if result:
                        Doc.objects.filter(id=pro.doc.id).update(plant_list=None)
                        pro.delete()
                        return JsonResponse({'status': True, 'data': '删除成功！'})

                    return JsonResponse({'status':False, 'data': '删除失败！'})
                else:
                    return JsonResponse({'status':False,'data':'非法请求'})
            elif range == 'multi':
                # docs = doc_publish_id.split(",")
                # try:
                #     DocPublishData.objects.filter(id__in=docs,create_user=request.user).update(status=3,modify_time=datetime.datetime.now())
                #     Doc.objects.filter(parent_doc__in=docs).update(status=3,modify_time=datetime.datetime.now())
                #     return JsonResponse({'status': True, 'data': '删除完成'})
                # except:
                return JsonResponse({'status': False, 'data': '当前功能还未完成！'})
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
    all_result = {}
    plant_name_list = []
    try:
        doc = Doc.objects.filter(id=int(doc_id), create_user=request.user)
        doc_create_user = doc[0].create_user
        doc_name = doc[0].name
        doc_pre_content = doc[0].pre_content
        # 已发布平台
        # doc_plant_list = doc[0].plant_list
        editor_mode = doc[0].editor_mode
        doc_content = doc[0].content
        doc_status = doc[0].status
        doc_plant_name_list = DocPublishData.objects.filter(doc=doc[0])
        if doc_plant_name_list:
            for data in doc_plant_name_list:
                plant_name_list.append(data.plant_name)
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
        for plant_info in cookie:
            cookie_user = plant_info.create_user
            plant_cookie = plant_info.cookie
            plant_name = plant_info.plant.plant_name
            all_result[plant_name] = {}
            plant_config = PlatformConfiguration.objects.filter(create_user=request.user, plant__plant_name=plant_name)
            if not plant_config or (plant_config and not plant_config[0].tags):
                all_result[plant_name] = f'<b>{plant_name}</b> 没有配置文章标签，请配置文章标签后重新发布！'
                continue
            if plant_name_list and plant_name in plant_name_list:
                all_result[plant_name] = f'<b>{plant_name}</b> 渠道已发布'
                continue
            result, publish_url, pub_status = pub_spider(plant_name, plant_cookie, doc_tags=doc_tags, doc_name=doc_name,
                                                         doc_pre_content=doc_pre_content,  doc_content=doc_content,
                                                         plant_config=plant_config, is_markdown=is_markdown)
            if result == 'need_login':
                cookie.update(status=0)
                pub_status = 0
                all_result[plant_name] = f'<b>{plant_name}</b>，请更换 cookie 后重新发布'
                continue
                # return JsonResponse({'status': False, 'data': '发布失败，请更换 cookie 后重新发布！'})
            if result:
                DocPublishData.objects.create(
                    doc=doc[0],
                    plant_name=plant_name,
                    doc_publish_url=publish_url,
                    status=pub_status,
                    create_user=request.user
                )
            if pub_status == 1:
                all_result[plant_name] = f'<b>{plant_name}</b> 渠道分发成功'
            else:
                all_result[plant_name] = f'<b>{plant_name}</b> 渠道分发失败'
        return JsonResponse({'status': True, 'data': '发布已完成！', 'result': all_result})

    except ObjectDoesNotExist:
        return JsonResponse({'status': False, 'data': '当前平台不存在'})
    except:
        print(traceback.format_exc())
        return JsonResponse({'status': False, 'data': '系统异常', 'result': all_result})


def pub_spider(plant_name, plant_cookie, **kwargs):
    doc_tags = kwargs.get('doc_tags')
    doc_name = kwargs.get('doc_name')
    doc_pre_content = kwargs.get('doc_pre_content')
    doc_content = kwargs.get('doc_content')
    plant_config = kwargs.get('plant_config')
    is_markdown = kwargs.get('is_markdown')
    publish_url, pub_status, result = None, None, None
    if plant_name == 'CSDN':
        result = CSDNPublish(plant_cookie).publish_content(tags=doc_tags, title=doc_name,
                                                           markdowncontent=doc_pre_content,
                                                           content=doc_content, plant_config=plant_config)
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
                                         markdowncontent=doc_pre_content, is_markdown=is_markdown,
                                         plant_config=plant_config)
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
        result = seg_pub.publish_content(tags=doc_tags, markdowncontent=doc_pre_content, title=doc_name,
                                         plant_config=plant_config)
        if result and result == 'need_login':
            pub_status = 0
        else:
            try:
                r_json = json.loads(result)
            except:
                print(result, '=============')
                pub_status = 0
            else:
                msg = r_json.get('msg')
                title = r_json.get('title')
                seg_data = r_json.get('data')
                if seg_data:
                    article_id = seg_data.get('id')
                    publish_url = 'https://segmentfault.com/a/' + str(article_id)
                    pub_status = 1
                else:
                    pub_status = 0
            # article_status = r_json.get('data').get('status')

    elif plant_name == '知乎':

        zhi_hu_pub = ZhiHuPublish(cookie=plant_cookie)
        result = zhi_hu_pub.publish_content(tags=doc_tags, title=doc_name, content=doc_content,
                                            plant_config=plant_config)

        r_json = json.loads(result)
        publish_url = r_json.get('url')
        title = r_json.get('title')
        seg_data = r_json.get('data')
        pub_status = 1
    elif plant_name == '掘金':
        jue_jin_pub = JueJinPublish(cookie=plant_cookie)
        result = jue_jin_pub.publish_content(tags=doc_tags, title=doc_name, markdowncontent=doc_content,
                                             plant_config=plant_config)
        r_json = json.loads(result)
        article_id = r_json.get('data').get('article_id')
        publish_url = 'https://juejin.cn/post/' + str(article_id)
        pub_status = 1

    # else:
    #     result = None
    #     return False
    return result, publish_url, pub_status


# 图床管理
@login_required()
@logger.catch()
def drawing_bed_setting(request):
    # 图床管理页面
    try:
        if get_drawing_beds(request, 'upyun'):
            upyun_access_key, upyun_secret_key, upyun_storage_space_name, upyun_visit_website, upyun_url_suffix, \
            upyun_storage_path, upyun_default_types = get_drawing_beds(request, types='upyun')
        if get_drawing_beds(request, 'qiniu'):
            qiniu_access_key, qiniu_secret_key, qiniu_storage_space_name, qiniu_visit_website, qiniu_storage_area, \
            qiniu_url_suffix, qiniu_storage_path, qiniu_default_types = get_drawing_beds(request, types='qiniu')
        if request.method == 'GET':
            return render(request, 'app_doc/manage/manage_drawing_bed_setting.html', locals())
        elif request.method == 'POST':
            types = request.POST.get('type', None)
            access_key = request.POST.get('access_key', None)  # ak
            secret_key = request.POST.get('secret_key', None)  # sk
            storage_space_name = request.POST.get('storage_space_name', None)  # 存储空间名
            visit_website = request.POST.get('visit_website', None)  # 访问网址
            storage_area = request.POST.get('storage_area', None)  # 存储区域
            url_suffix = request.POST.get('url_suffix', None)  # 网址后缀
            storage_path = request.POST.get('storage_path', None)  # 存储路径
            default_types = request.POST.get('default_types', None)  # 存储路径
            # 基础设置
            if types == 'qiniu':
                if access_key and secret_key and storage_space_name and visit_website and storage_area:
                    drawing_bed_save_setting(request, access_key, secret_key, storage_space_name,
                                             visit_website, url_suffix, storage_path, storage_area, default_types,
                                             types)
                    qiniu_access_key, qiniu_secret_key, qiniu_storage_space_name, qiniu_visit_website, qiniu_storage_area, \
                    qiniu_url_suffix, qiniu_storage_path, qiniu_default_types = get_drawing_beds(request, types=types)
                    return render(request, 'app_doc/manage/manage_drawing_bed_setting.html', locals())
                else:
                    return JsonResponse({'status': False, 'data': '缺少必要参数！'})
            # 又拍云
            if types == 'upyun':
                if access_key and secret_key and storage_space_name and visit_website:
                    drawing_bed_save_setting(request, access_key, secret_key, storage_space_name,
                                             visit_website, url_suffix, storage_path, storage_area, default_types,
                                             types)
                    upyun_access_key, upyun_secret_key, upyun_storage_space_name, upyun_visit_website, upyun_url_suffix, \
                    upyun_storage_path, upyun_default_types = get_drawing_beds(request, types=types)
                    return render(request, 'app_doc/manage/manage_drawing_bed_setting.html', locals())
                else:
                    return JsonResponse({'status': False, 'data': '缺少必要参数！'})

    except:
        print(traceback.format_exc())
        return JsonResponse({'status': False, 'data': '请求错误！'})


def get_drawing_beds(request, types):
    if types == 'upyun':
        upyun_settings = DrawingBedSetting.objects.filter(types=types, create_user=request.user)
        if upyun_settings.count() == 8:
            upyun_access_key = upyun_settings.get(name=f'{types}_access_key')
            upyun_secret_key = upyun_settings.get(name=f'{types}_secret_key')
            upyun_storage_space_name = upyun_settings.get(name=f'{types}_storage_space_name')
            upyun_visit_website = upyun_settings.get(name=f'{types}_visit_website')
            upyun_url_suffix = upyun_settings.get(name=f'{types}_url_suffix')
            upyun_storage_path = upyun_settings.get(name=f'{types}_storage_path')
            upyun_default_types = upyun_settings.get(name=f'{types}_default_types')
            return upyun_access_key, upyun_secret_key, upyun_storage_space_name, \
                   upyun_visit_website, upyun_url_suffix, upyun_storage_path, upyun_default_types
    if types == "qiniu":
        qiniu_settings = DrawingBedSetting.objects.filter(types=types, create_user=request.user)
        if qiniu_settings.count() == 8:
            qiniu_access_key = qiniu_settings.get(name=f'{types}_access_key')
            qiniu_secret_key = qiniu_settings.get(name=f'{types}_secret_key')
            qiniu_storage_space_name = qiniu_settings.get(name=f'{types}_storage_space_name')
            qiniu_visit_website = qiniu_settings.get(name=f'{types}_visit_website')
            qiniu_storage_area = qiniu_settings.get(name=f'{types}_storage_area')
            qiniu_url_suffix = qiniu_settings.get(name=f'{types}_url_suffix')
            qiniu_storage_path = qiniu_settings.get(name=f'{types}_storage_path')
            qiniu_default_types = qiniu_settings.get(name=f'{types}_default_types')
            return qiniu_access_key, qiniu_secret_key, qiniu_storage_space_name, \
                   qiniu_visit_website, qiniu_storage_area, qiniu_url_suffix, qiniu_storage_path, qiniu_default_types


def drawing_bed_save_setting(request, access_key, secret_key, storage_space_name, visit_website,
                             url_suffix, storage_path, storage_area, default_types, types):
    # 更新sk
    DrawingBedSetting.objects.update_or_create(
        name=f'{types}_access_key',
        defaults={'value': access_key, 'types': types, 'create_user': request.user}
    )
    # 更新sk
    DrawingBedSetting.objects.update_or_create(
        name=f'{types}_secret_key',
        defaults={'value': secret_key, 'types': types, 'create_user': request.user}
    )
    # 更新存储空间名
    DrawingBedSetting.objects.update_or_create(
        name=f'{types}_storage_space_name',
        defaults={'value': storage_space_name, 'types': types, 'create_user': request.user}
    )
    # 更新访问网址
    DrawingBedSetting.objects.update_or_create(
        name=f'{types}_visit_website',
        defaults={'value': visit_website, 'types': types, 'create_user': request.user}
    )
    # 更新存储区域
    DrawingBedSetting.objects.update_or_create(
        name=f'{types}_storage_area',
        defaults={'value': storage_area, 'types': types, 'create_user': request.user}
    )
    # 更新网址后缀
    DrawingBedSetting.objects.update_or_create(
        name=f'{types}_url_suffix',
        defaults={'value': url_suffix, 'types': types, 'create_user': request.user}
    )
    # 更新存储路径
    DrawingBedSetting.objects.update_or_create(
        name=f'{types}_storage_path',
        defaults={'value': storage_path, 'types': types, 'create_user': request.user}
    )
    # 更新是否为默认图床
    DrawingBedSetting.objects.update_or_create(
        name=f'{types}_default_types',
        defaults={'value': default_types, 'types': types, 'create_user': request.user}
    )
    if default_types:
        # 当前默认图床如果有值，则修改其他图床的默认值为None
        DrawingBedSetting.objects.exclude(types=types,
                                          create_user=request.user).filter(
            name__contains='default_types').update(value=None)


# 文章分发 ----- 获取文章阅读数、评论数点赞数
@login_required()
@require_POST
@logger.catch(reraise=True)
def article_all_num(request):
    return JsonResponse({'status': False, 'data': '该功能还在完善中！'})


# 用户查看的发布平台配置
@login_required()
@logger.catch()
def plant_config_manage(request):
    try:
        if request.method == 'GET':
            return render(request, 'app_doc/manage/manage_plant_config.html', locals())
        elif request.method == 'POST':
            page = request.POST.get('page', 1)
            type = request.POST.get('type', None)
            if type and type == 'delete':
                config_id = request.POST.get('config_id', 1)
                PlatformConfiguration.objects.filter(create_user=request.user, id=int(config_id)).delete()
                return JsonResponse({'status': True, 'data': '删除成功！'})

            limit = request.POST.get('limit', 10)
            plant_config_list = PlatformConfiguration.objects.filter(create_user=request.user)
            # 分页处理
            paginator = Paginator(plant_config_list, limit)
            page = request.GET.get('page', page)
            try:
                docs_push = paginator.page(page)
            except PageNotAnInteger:
                docs_push = paginator.page(1)
            except EmptyPage:
                docs_push = paginator.page(paginator.num_pages)

            # project_list = DocPublishData.objects.filter(create_user=request.user).order_by('-create_time')
            table_data = []
            for project in docs_push:
                item = {
                    'id': project.id,
                    'plant_name': project.plant.plant_name,
                    'category': project.category_name,
                    'sub_category': project.sub_category_name,
                    'tags': project.tags,
                    'art_type': project.art_type,
                    'art_source_url': project.art_source_url,
                    'art_publish_type': project.art_publish_type,
                    'create_time': project.create_time,
                }
                table_data.append(item)
            resp_data = {
                "code": 0,
                "msg": "ok",
                "count": plant_config_list.count(),
                "data": table_data
            }
            return JsonResponse(resp_data)
    except:
        print(traceback.format_exc())
        return JsonResponse({'status': False, 'data': '请求错误！'})


@login_required()
@require_POST
@logger.catch()
def add_plant_config(request):
    if request.method == 'POST':
        # print('===============')
        plant_name = request.POST.get('plant', None)
        plant_config = request.POST.get('plant_config', None)
        category_name = request.POST.get('category_name', None)
        category_value = request.POST.get('category', None)
        sub_category_name = request.POST.get('sub_category_name', None)
        sub_category_value = request.POST.get('sub_category', None)
        tags = request.POST.get('inputTags', None)
        # 文章类型（原创、转载、翻译）
        art_type = request.POST.get('art_type', None)
        # 转载和翻译的需要输入文章来源
        art_source_url = request.POST.get('art_source_url', None)
        # 发布形式
        art_publish_type = request.POST.get('art_pub_type', None)
        if not category_value:
            category_name = ''
        if not sub_category_value:
            sub_category_name = ''
        if art_type in ['2', '3'] and not art_source_url:
            return JsonResponse({'status': False, 'data': '请输入文章来源！'})
        if plant_config:
            PlatformConfiguration.objects.filter(
                id=int(plant_config), create_user=request.user).update(category_name=category_name,
                                                                       category_value=category_value,
                                                                       sub_category_name=sub_category_name,
                                                                       sub_category_value=sub_category_value,
                                                                       tags=tags, art_type=art_type,
                                                                       art_source_url=art_source_url,
                                                                       art_publish_type=art_publish_type)
            return JsonResponse({'status': True, 'data': '更新成功！'})
        if plant_name and art_type:
            plant = Plant.objects.filter(plant_name=plant_name)
            if not plant:
                return JsonResponse({'status': False, 'data': '非法请求！'})
            check_result = PlatformConfiguration.objects.filter(create_user=request.user, plant=plant[0])
            if check_result:
                return JsonResponse({'status': False, 'data': '当前平台配置已存在！'})
            PlatformConfiguration.objects.update_or_create(
                plant=plant[0],
                category_name=category_name,
                category_value=category_value,
                sub_category_name=sub_category_name,
                sub_category_value=sub_category_value,
                tags=tags,
                art_type=art_type,
                art_source_url=art_source_url,
                art_publish_type=art_publish_type,
                create_user=request.user
            )
            return JsonResponse({'status': True, 'data': '添加成功！'})

        return JsonResponse({'status': False, 'data': '请求错误！'})


# 增加发布平台配置页面
@login_required()
@logger.catch()
def plant_config_html(request, config_id):
    # 每个用户的发布平台配置
    if request.method == 'GET':
        if config_id:
            # print('config_id:', config_id)
            plant_config = PlatformConfiguration.objects.filter(id=int(config_id), create_user=request.user)[0]
            plant_list = Plant.objects.all()
            return render(request, 'app_doc/manage/manage_plant_config_iframe.html', locals())
        else:
            plant_list = Plant.objects.all()
            return render(request, 'app_doc/manage/manage_plant_config_iframe.html', locals())


# 增加发布平台自有的相关信息
@login_required()
@logger.catch()
def api_plant_config(request):
    # 每个用户的发布平台配置
    if request.method == 'POST':
        plant_value = request.POST.get('plant_value', None)
        type_name = request.POST.get('type_name', None)
        CookiePlant.objects.filter(create_user=request.user, plant__plant_name=plant_value)
        if plant_value and type_name:
            cookie_info = CookiePlant.objects.filter(create_user=request.user, plant__plant_name=plant_value)
            if not cookie_info:
                return JsonResponse({'status': False, 'data': '请先完善该平台cookie！'})
            # check_result = PlatformConfiguration.objects.filter(create_user=request.user, plant__plant_name=plant_value)
            # if check_result:
            #     return JsonResponse({'status': False, 'data': '当前平台配置已存在！'})
            plant_cookie = cookie_info[0].cookie
            # print(plant_value, '123445')
            if plant_value == 'CSDN':
                if type_name == 'category':
                    category_list = CSDNPublish(cookie=plant_cookie).get_category()
                    if category_list is None:
                        return JsonResponse({'status': False, 'data': '获取分类失败，请检查cookie是否正确！'})
                    return JsonResponse({'status': True, 'data': category_list})
            if plant_value == '博客园':
                if type_name == 'category':
                    category_list = CNBlogPublish(cookie=plant_cookie).get_blog_cate()
                    if category_list is None:
                        return JsonResponse({'status': False, 'data': '获取分类失败，请检查cookie是否正确！'})
                    return JsonResponse({'status': True, 'data': category_list})
            if plant_value == '掘金':
                if type_name == 'category':
                    category_list = JueJinPublish(cookie=plant_cookie).get_category()
                    if category_list is None:
                        return JsonResponse({'status': False, 'data': '获取分类失败，请检查cookie是否正确！'})
                    return JsonResponse({'status': True, 'data': category_list})
            # if plant_value == '知乎'

        return render(request, 'app_doc/manage/manage_plant_config_iframe.html', locals())



