# coding:utf-8
# @文件: serializers_app.py
# @创建者：州的先生
# #日期：2020/5/11
# 博客地址：zmister.com

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer,SerializerMethodField
from app_doc.models import *

# 文集序列化器
class ProjectSerializer(ModelSerializer):
    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M')

    class Meta:
        model = Project
        fields = ('__all__')

# 文档序列化器
class DocSerializer(ModelSerializer):

    project_name = SerializerMethodField(label="所属文集")
    modify_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = Doc
        fields = ('__all__')

    # 返回文档的所属文集
    def get_project_name(self,obj):
        pro_name = Project.objects.get(id=obj.top_doc).name
        return pro_name

# 文档模板序列化器
class DocTempSerializer(ModelSerializer):
    class Meta:
        model = DocTemp
        fields = ('__all__')

# 图片序列化器
class ImageSerializer(ModelSerializer):
    class Meta:
        model = Image
        fields = ('__all__')

# 图片分组序列化器
class ImageGroupSerializer(ModelSerializer):
    class Meta:
        model = ImageGroup
        fields = ('__all__')

# 附件序列化器
class AttachmentSerializer(ModelSerializer):
    class Meta:
        model = Attachment
        fields = ('__all__')