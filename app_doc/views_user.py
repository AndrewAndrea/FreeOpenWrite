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
from django.utils.translation import gettext_lazy as _
from app_doc.models import Project,Doc,DocTemp
from django.contrib.auth.models import User

from django.db.models import Q
from django.urls import reverse
from django.views.decorators.http import require_POST
from loguru import logger
from app_doc.report_utils import *

from app_admin.models import Plant
from app_doc.models import DocBottomConfiguration

import traceback
import re
import json


# 替换前端传来的非法字符
from app_doc.views_doc_pub import pub_spider


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
                plant_cookie = request.POST.get('plant_cookie', None)  # cookie
                plant_id = request.POST.get('plant_id', None)  # 平台id
                if not plant_cookie or not plant_id:
                    return JsonResponse({'status': False, 'data': '新增失败！'})
                plant = Plant.objects.filter(id=int(plant_id), status=1)
                if plant:
                    is_true = CookiePlant.objects.filter(plant=plant[0], create_user=request.user)
                    if is_true:
                        return JsonResponse({'status': False, 'data': f'新增失败！<b>{plant[0].plant_name}</b> cookie已存在！'})
                    # 创建一个 cookie
                    CookiePlant.objects.create(
                        cookie=plant_cookie,
                        plant=plant[0],
                        status=1,
                        create_user=request.user
                    )
                    return JsonResponse({'status': True, 'data': f'<b>{plant[0].plant_name}</b> cookie新增成功'})
                else:
                    return JsonResponse({'status': False, 'data': f'<b>{plant[0].plant_name}</b>新增失败！当前平台不可用！'})
            except Exception as e:
                logger.exception("新增发布平台异常")
                return JsonResponse({'status': False, 'data': '系统异常'})
        elif int(types) == 2:  # 更新 cookie
            code_id = request.POST.get('code_id', None)
            cookie = request.POST.get('cookie', None)
            plant_id = request.POST.get('plant_id', None)  # 平台id
            if not cookie:
                return JsonResponse({'status': False, 'data': '更新失败！'})
            try:
                if plant_id:
                    plant_result = Plant.objects.filter(id=int(plant_id), status=1)
                    CookiePlant.objects.filter(plant=plant_result[0], create_user=request.user).update(status=1,
                                                                                                       cookie=cookie)
                    plant_name = plant_result[0].plant_name
                else:
                    cookie_result = CookiePlant.objects.filter(id=int(code_id))
                    cookie_result.update(status=1, cookie=cookie)
                    plant_name = cookie_result[0].plant.plant_name
                # print(register_code)
                return JsonResponse({'status': True, 'data': f'<b>{plant_name}</b> cookie 更新成功！'})
            except ObjectDoesNotExist:
                return JsonResponse({'status': False, 'data': '当前平台不存在'})
            except:
                print(traceback.format_exc())
                return JsonResponse({'status': False, 'data': '系统异常'})
        elif int(types) == 3:  # 当前cookie 存在则更新，不存在则添加
            cookie = request.POST.get('cookie', None)
            plant_name = request.POST.get('plant_name', None)  # 平台id
            if not plant_name:
                return JsonResponse({'status': False, 'data': '异常请求！'})
            try:
                plant_result = Plant.objects.filter(plant_name=plant_name, status=1)
                is_cookie = CookiePlant.objects.filter(plant=plant_result[0], create_user=request.user)
                if not cookie:
                    return JsonResponse({'status': False, 'data': f'<b>{plant_result[0].plant_name}</b> 没有登陆哦！'})
                if is_cookie:
                    is_cookie.update(status=1, cookie=cookie)
                else:
                    # 创建一个 cookie
                    CookiePlant.objects.create(
                        cookie=cookie,
                        plant=plant_result[0],
                        status=1,
                        create_user=request.user
                    )

                plant_name = plant_result[0].plant_name

                # print(register_code)
                return JsonResponse({'status': True, 'data': f'<b>{plant_name}</b> cookie 获取成功！'})
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
    plant_name_list = []
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
        doc_plant_name_list = DocPublishData.objects.filter(doc=doc[0])
        if doc_plant_name_list:
            for data in doc_plant_name_list:
                plant_name_list.append(data.plant_name)
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
        plant_config = PlatformConfiguration.objects.filter(create_user=request.user, plant__plant_name=plant_name)
        if doc_create_user == cookie_user and cookie_user == request.user:
            result, publish_url, pub_status = pub_spider(plant_name, plant_cookie, doc_tags=doc_tags, doc_name=doc_name,
                                                         doc_pre_content=doc_pre_content, doc_content=doc_content,
                                                         plant_config=plant_config, is_markdown=is_markdown)
            if result == 'need_login':
                cookie.update(status=0)
                return JsonResponse({'status': False, 'data': '发布失败，请更换 cookie 后重新发布！'})
            if result and pub_status == 0:
                return JsonResponse({'status': False, 'data': result})
            if result and pub_status == 1:
                DocPublishData.objects.create(
                    doc=doc[0],
                    plant_name=plant_name,
                    doc_publish_url=publish_url,
                    status=pub_status,
                    create_user=request.user
                )
                return JsonResponse({'status': True, 'data': '发布成功'})
            return JsonResponse({'status': False, 'data': '发布失败!cookie 失效或没有设置文章标签'})
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
            "title": _("仪表盘"),
            "type": 1,
            "icon": "layui-icon layui-icon-console",
            "href": reverse('manage_overview'),
        },
        {
            "id": "my_plant_manage",
            "title": _("渠道分发"),
            "icon": "layui-icon layui-icon-component",
            "type": 0,
            "href": "",
            "children": [
                {
                    "id": "doc_cookie_manage",
                    "title": _("文章分发"),
                    "icon": "layui-icon layui-icon-face-smile",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("cookie_manage")
                },
                {
                    "id": "doc_publish_manage",
                    "title": _("分发数据"),
                    "icon": "layui-icon layui-icon-face-smile",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("doc_publish_manage")
                },
                {
                    "id": "plant_config_manage",
                    "title": _("渠道配置"),
                    "icon": "layui-icon layui-icon-face-smile",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("plant_config_manage")
                },
                {
                    "id": "bottom_template_manage",
                    "title": _("底部模板"),
                    "icon": "layui-icon layui-icon-face-smile",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("bottom_template_manage")
                },
                {
                    "id": "drawing_bed_setting",
                    "title": _("图床配置"),
                    "icon": "layui-icon layui-icon-face-smile",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("drawing_bed_setting")
                },
            ]
        },
        {
            "id": "my_project",
            "title": _("我的文集"),
            "icon": "layui-icon layui-icon-component",
            "type": 0,
            "href": "",
            "children": [
                {
                    "id": "manage_project",
                    "title": _("文集管理"),
                    "icon": "layui-icon layui-icon-console",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse('manage_project')
                },
                {
                    "id": "manage_colla_self",
                    "title": _("我的协作"),
                    "icon": "layui-icon layui-icon-console",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse('manage_pro_colla_self')
                },
                {
                    "id": "import_project",
                    "title": _("导入文集"),
                    "icon": "layui-icon layui-icon-console",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse('import_project')
                },
            ]
        },
        {
            "id": "my_doc",
            "title": _("我的文档"),
            "icon": "layui-icon layui-icon-file-b",
            "type": 0,
            "href": "",
            "children": [
                {
                    "id": "doc_manage",
                    "title": _("文档管理"),
                    "icon": "layui-icon layui-icon-face-smile",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("manage_doc")
                },
                {
                    "id": "doc_template",
                    "title": _("文档模板"),
                    "icon": "layui-icon layui-icon-face-cry",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("manage_doctemp")
                },
                {
                    "id": "doc_tag",
                    "title": _("文档标签"),
                    "icon": "layui-icon layui-icon-face-cry",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("manage_doc_tag")
                },
                {
                    "id": "doc_share",
                    "title": _("我的分享"),
                    "icon": "layui-icon layui-icon-face-cry",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("manage_doc_share")
                },
                {
                    "id": "doc_recycle",
                    "title": _("文档回收站"),
                    "icon": "layui-icon layui-icon-face-cry",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("doc_recycle")
                }
            ]
        },
        {
            "id": "my_fodder",
            "title": _("我的素材"),
            "icon": "layui-icon layui-icon-upload-drag",
            "type": 0,
            "href": "",
            "children": [
                {
                    "id": "my_img",
                    "title": _("我的图片"),
                    "icon": "layui-icon layui-icon-face-smile",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("manage_image")
                },
                {
                    "id": "my_attachment",
                    "title": _("我的附件"),
                    "icon": "layui-icon layui-icon-face-cry",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("manage_attachment")
                },
            ]
        },
        {
            "id": "my_collect",
            "title": _("我的收藏"),
            "icon": "layui-icon layui-icon-star",
            "type": 1,
            "openType": "_iframe",
            "href": reverse("manage_collect")
        },
        {
            "id": "self_settings",
            "title": _("个人管理"),
            "icon": "layui-icon layui-icon-set-fill",
            "type": 0,
            "href": "",
            "children": [
                {
                    "id": 601,
                    "title": _("个人设置"),
                    "icon": "layui-icon layui-icon-face-smile",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("manage_self")
                },
                {
                    "id": 602,
                    "title": _("Token管理"),
                    "icon": "layui-icon layui-icon-face-cry",
                    "type": 1,
                    "openType": "_iframe",
                    "href": reverse("manage_token")
                },
            ]
        },
        {
            "id": "user_manual",
            "title": _("使用手册"),
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
