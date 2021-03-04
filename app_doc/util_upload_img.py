# coding:utf-8
import traceback
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth.decorators import login_required # 登录需求装饰器
import datetime,time,json,base64,os,uuid
from app_doc.models import Image,ImageGroup,Attachment

from app_admin.models import SysSetting, DrawingBedSetting
import requests
import random
from qiniu import Auth, put_data


@login_required()
@csrf_exempt
def upload_ice_img(request):
    ##################
    # 如果需要使用ice自带的多文件上传，请修改ice的js文件中的附件上传部分代码如下：
    # 
    # for(var i=0;i<this.files.length;i++){
    # 	formData.append('file_' + i, this.files[i]);
    # }
    # formData.append('upload_num', i);
    # formData.append('upload_type', "files");
    ##################
    try:
        up_type = request.POST.get('upload_type', '')
        up_num = request.POST.get('upload_num', '')
        iceEditor_img = str(request.POST.get('iceEditor-img', ''))
    except:
        pass
    if up_type == "files":
        # 多文件上传功能，需要修改js文件
        res_dic = {'length': int(up_num)}
        for i in range(0, int(up_num)):
            file_obj = request.FILES.get('file_' + str(i))
            result = ice_save_file(file_obj, request.user)
            res_dic[i] = result
    elif iceEditor_img.lower().startswith('http'):
        res_dic = ice_url_img_upload(iceEditor_img, request.user)
    else:
        # 粘贴上传和单文件上传
        file_obj = request.FILES.get('file[]')
        result = ice_save_file(file_obj, request.user)
        res_dic = {0: result, "length": 1, 'other_msg': iceEditor_img}  # 一个文件，直接把文件数量固定了
    return HttpResponse(json.dumps(res_dic), content_type="application/json")


def ice_save_file(file_obj,user):   

    # 默认保留支持ice单文件上传功能，可以iceEditor中开启
    file_suffix = str(file_obj).split(".")[-1]  # 提取图片格式
    # 允许上传文件类型，ice粘贴上传为blob
    allow_suffix = ["jpg", "jpeg", "gif", "png", "bmp", "webp", "blob"]
    # 判断附件格式
    is_images = ["jpg", "jpeg", "gif", "png", "bmp", "webp"]
    if file_suffix.lower() not in allow_suffix:
        return {"error": "文件格式不允许"}
    if file_suffix.lower() == 'blob':
        # 粘贴上传直接默认为png就行
        file_suffix = 'png'
        # 接下来构造一个文件名，时间和随机10位字符串构成
    relative_path = upload_generation_dir()
    name_time = time.strftime("%Y-%m-%d_%H%M%S_")
    name_join = ""
    name_rand = name_join.join(random.sample('zyxwvutsrqponmlkjihgfedcba', 10))

    file_name = name_time + name_rand + "." + file_suffix
    path_file = relative_path + file_name
    path_file = settings.MEDIA_ROOT + path_file
    #file_Url 是文件的url下发路径
    file_url = (settings.MEDIA_URL + relative_path + file_name).replace("//","/")
    

    with open(path_file, 'wb') as f:
        for chunk in file_obj.chunks():
            f.write(chunk)  # 保存文件
        if file_suffix.lower() in is_images:
            Image.objects.create(
                user=user,
                file_path=file_url,
                file_name=file_name,
                remark="iceEditor上传"
            )

        
        else :
            #文件上传，暂时不屏蔽，如果需要正常使用此功能，是需要在iceeditor中修改的，mrdoc使用的是自定义脚本上传

            Attachment.objects.create(
                user=user,
                file_path=file_url,
                file_name=file_name,
                file_size=str(round(len(chunk) / 1024, 2)) + "KB"
            )

        return  {"error":0, "name": str(file_obj),'url':file_url}

    return {"error": "文件存储异常"}


# ice_url图片上传
def ice_url_img_upload(url, user):
    relative_path = upload_generation_dir()
    name_time = time.strftime("%Y-%m-%d_%H%M%S_")
    name_join = ""
    name_rand = name_join.join(random.sample('zyxwvutsrqponmlkjihgfedcba', 10))
    file_name = name_time + name_rand + '.png'  # 日期时间_随机字符串命名
    path_file = os.path.join(relative_path, file_name)
    path_file = settings.MEDIA_ROOT + path_file
    # print('文件路径：', path_file)
    file_url = (settings.MEDIA_URL + relative_path + file_name).replace("//","/")
    # print("文件URL：", file_url)
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
    }
    r = requests.get(url, headers=header, stream=True)

    if r.status_code == 200:
        with open(path_file, 'wb') as f:
            f.write(r.content)  # 保存文件
        Image.objects.create(
            user=user,
            file_path=file_url,
            file_name=file_name,
            remark='iceurl粘贴上传',
        )
    resp_data = {"error": 0, "name": file_name, 'url': file_url}
    return resp_data


@login_required()
@csrf_exempt
def upload_img(request):
    ##################
    # {"success": 0, "message": "出错信息"}
    # {"success": 1, "url": "图片地址"}
    ##################
    dbs = DrawingBedSetting.objects.filter(name="default_types", value__isnull=False)
    bed_default_types = "basic"
    if dbs.count() != 0:
        bed_default_types = dbs.get(name="default_types").types
    img = request.FILES.get("editormd-image-file", None)  # 编辑器上传
    manage_upload = request.FILES.get('manage_upload', None)  # 图片管理上传
    try:
        url_img = json.loads(request.body.decode())['url']
    except:
        url_img = None
    dir_name = request.POST.get('dirname', '')
    base_img = request.POST.get('base', None)
    group_id = request.POST.get('group_id', 0)

    if int(group_id) not in [0, -1]:
        try:
            group_id = ImageGroup.objects.get(id=group_id)
        except:
            group_id = None
    else:
        group_id = None

    # 上传普通图片文件
    if img:
        result = img_upload(img, dir_name, request.user, bed_default_types)
    # 图片管理上传
    elif manage_upload:
        result = img_upload(manage_upload, dir_name, request.user, bed_default_types,
                            group_id=group_id)
    # 上传base64编码图片
    elif base_img:
        result = base_img_upload(base_img, dir_name, request.user, bed_default_types)
    # 上传图片URL地址
    elif url_img:
        if url_img.startswith("data:image"):  # 以URL形式上传的BASE64编码图片
            result = base_img_upload(url_img, dir_name, request.user, bed_default_types)
        else:
            result = url_img_upload(url_img, dir_name, request.user, bed_default_types)
    else:
        result = {"success": 0, "message": "上传出错"}
    return HttpResponse(json.dumps(result), content_type="application/json")



# 目录创建
def upload_generation_dir(dir_name=''):
    today = datetime.datetime.today()
    dir_name = dir_name + '/%d%02d/' % (today.year, today.month)
    # print("dir_name:",dir_name)
    if not os.path.exists(settings.MEDIA_ROOT + dir_name):
        # print("创建目录")
        os.makedirs(settings.MEDIA_ROOT + dir_name)
    return dir_name


# 普通图片上传
def img_upload(files, dir_name, user, bed_default_types, group_id=None):
    # 允许上传文件类型
    allow_suffix = ["jpg", "jpeg", "gif", "png", "bmp", "webp"]
    file_suffix = files.name.split(".")[-1]  # 提取图片格式
    # 判断图片格式
    if file_suffix.lower() not in allow_suffix:
        return {"success": 0, "message": "图片格式不正确"}

    # 判断图片的大小
    try:
        allow_image_size = SysSetting.objects.get(types='doc', name='img_size')
        allow_img_size = int(allow_image_size.value) * 1048576
    except Exception as e:
        # print(repr(e))
        allow_img_size = 10485760
    if files.size > allow_img_size:
        return {"success": 0, "message": "图片大小超出{}MB".format(allow_img_size / 1048576)}

    relative_path = upload_generation_dir(dir_name)
    file_name = files.name.replace(file_suffix, '').replace('.', '') + '_' + str(int(time.time())) + '.' + file_suffix
    if bed_default_types == 'qiniu':
        file_url = upload_qiniu(file_name, files.read())
        if file_url is False:
            return {"success": 0, "message": "上传七牛云失败，请检查配置信息是否正确！"}
    else:
        path_file = os.path.join(relative_path, file_name)
        path_file = settings.MEDIA_ROOT + path_file
        file_url = (settings.MEDIA_URL + relative_path + file_name).replace("//",'/')
        # print("文件URL：",file_url)
        with open(path_file, 'wb') as f:
            for chunk in files.chunks():
                f.write(chunk)  # 保存文件
    Image.objects.create(
        user=user,
        file_path=file_url,
        file_name=file_name,
        remark='本地上传',
        group=group_id,
    )
    return {"success": 1, "url": file_url, 'message': '上传图片成功'}


# base64编码图片上传
def base_img_upload(files, dir_name, user, bed_default_types):
    files_str = files.split(';base64,')[-1]  # 截取图片正文
    files_base = base64.b64decode(files_str)  # 进行base64编码
    file_name = str(datetime.datetime.today()).replace(':', '').replace(' ', '_').split('.')[0] + '.png'  # 日期时间

    if bed_default_types == 'qiniu':
        file_url = upload_qiniu(file_name, files_base)
        if file_url is False:
            return {"success": 0, "message": "上传七牛云失败，请检查配置信息是否正确！"}
    else:
        relative_path = upload_generation_dir(dir_name)
        path_file = os.path.join(relative_path, file_name)
        path_file = settings.MEDIA_ROOT + path_file
        file_url = (settings.MEDIA_URL + relative_path + file_name).replace("//","/")
        # print("文件URL：", file_url)
        with open(path_file, 'wb') as f:
            f.write(files_base)  # 保存文件
    Image.objects.create(
        user=user,
        file_path=file_url,
        file_name=file_name,
        remark='粘贴上传',
    )
    return {"success": 1, "url": file_url, 'message': '上传图片成功'}


# url图片上传
def url_img_upload(url, dir_name, user, bed_default_types):
    relative_path = upload_generation_dir(dir_name)
    file_name = str(datetime.datetime.today()).replace(':', '').replace(' ', '_').split('.')[0] + '.png'  # 日期时间
    path_file = os.path.join(relative_path, file_name)
    path_file = settings.MEDIA_ROOT + path_file
    # print('文件路径：', path_file)
    file_url = (settings.MEDIA_URL + relative_path + file_name).replace("//","/")
    # print("文件URL：", file_url)
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
    }
    r = requests.get(url, headers=header, stream=True)

    if r.status_code == 200:
        if bed_default_types == 'qiniu':
            file_url = upload_qiniu(file_name, r.content)
            if file_url is False:
                return {"success": 0, "message": "上传七牛云失败，请检查配置信息是否正确！"}
        else:
            with open(path_file, 'wb') as f:
                f.write(r.content)  # 保存文件
        Image.objects.create(
            user=user,
            file_path=file_url,
            file_name=file_name,
            remark='粘贴上传',
        )
    resp_data = {
        'msg': '',
        'code': 0,
        'data': {
            'originalURL': url,
            'url': file_url
        }
    }
    return resp_data
    # return {"success": 1, "url": file_url, 'message': '上传图片成功'}


# 上传图片到七牛云
def upload_qiniu(img_name, files):
    qiniu_settings = DrawingBedSetting.objects.filter(types='qiniu')
    if qiniu_settings.count() == 8:
        access_key = qiniu_settings.get(name='access_key')
        secret_key = qiniu_settings.get(name='secret_key')
        storage_space_name = qiniu_settings.get(name='storage_space_name')
        visit_website = qiniu_settings.get(name="visit_website")
        storage_area = qiniu_settings.get(name="storage_area")
        url_suffix = qiniu_settings.get(name="url_suffix")
        storage_path = qiniu_settings.get(name="storage_path")
        default_types = qiniu_settings.get(name="default_types")
        access_key = access_key.value
        secret_key = secret_key.value
        # 构建鉴权对象
        q = Auth(access_key, secret_key)
        # 要上传的空间
        bucket_name = storage_space_name.value
        # 上传后保存的文件名
        key = storage_path.value + img_name
        # 生成上传 Token，可以指定过期时间等
        token = q.upload_token(bucket_name, key, 3600)
        # 要上传文件的本地路径
        ret, info = put_data(token, key, files)
        if ret and info:
            file_url = visit_website.value + '/' + ret.get('key') + url_suffix.value
            return file_url
        else:
            return False