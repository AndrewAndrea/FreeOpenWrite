// Ajax默认配置

layui.use(['table', 'jquery', 'form', 'layer', 'element'], function () {
            let table = layui.table;
            let form = layui.form;
            let $ = layui.jquery;
            let layer = layui.layer;
            let element = layui.element;
            $.ajaxSetup({
                data: {csrfmiddlewaretoken: '{{ csrf_token }}'},
            });
            // 新增cookie
            createRegisterCode = function () {
                layer.open({
                    type: 1,
                    title: '新增 cookie',
                    area: '300px;',
                    id: 'createRegCode',//配置ID
                    content: '<div style="margin:10px;"><input class="layui-input" id="plant_cookie" type="text" placeholder="输入平台 cookie"/><select name="plant_id" lay-verify="required"  lay-filter="plant" id="plant">\n' +
                        '                    <option value="">按平台筛选</option>\n' +
                        '                    {% for p in plant_list %}\n'+
                            '                        <option value="{{ p.id }}" >{{ p.plant_name }}</option>\n'+
                            '                    {% endfor %}\n' +
                        '                </select></div>',
                    btn: ['确定', '取消'], //添加按钮
                    btnAlign: 'c', //按钮居中
                    yes: function (index, layero) {
                        layer.load(1);
                        data = {
                            'types': 1,
                            'plant_cookie': $("#plant_cookie").val(),
                            'plant_id': $("#plant").val(),
                        }
                        $.post("{% url 'cookie_manage' %}", data, function (r) {
                            layer.closeAll('loading');
                            if (r.status) {
                                //新增成功，刷新页面
                                window.location.reload();
                                //layer.close(index)
                            } else {
                                //新增失败，提示
                                console.log(r)
                                layer.msg(r.data)
                            }
                        })
                    },
                });
            }
            //更新 cookie
            updateCookie = function (code_id) {
                layer.open({
                    type: 1,
                    title: '更新cookie',
                    area: '300px;',
                    id: 'updateCookie',//配置ID
                    content: '<div style="margin:10px;"><input class="layui-input" id="newCookie" type="text" placeholder="输入新的 cookie"/></div>',
                    btn: ['确定', '取消'], //添加按钮
                    btnAlign: 'c', //按钮居中
                    yes: function (index, layero) {
                        data = {
                            'types': 2,
                            'code_id': code_id,
                            'cookie': $("#newCookie").val()
                        }
                        $.post("{% url 'cookie_manage' %}", data, function (r) {
                            if (r.status) {
                                //删除成功，刷新页面
                                // {#window.location.reload();#}
                                layer.msg(r.data, function () {
                                    window.location.reload();
                                });
                                //layer.close(index)
                            } else {
                                //删除失败，提示
                                console.log(r)
                                layer.msg(r.data)
                            }
                        })
                    },
                });
            }
            // 文章分发
            publishCookie = function (code_id, plant_name) {
                var doc_id = '';
                var tags = '';
                var categorys = '';
                $.ajaxSetup({
                data: {csrfmiddlewaretoken: '{{ csrf_token }}'},
            });
                layer.open({
                    type: 1,
                    title: '文章分发',
                    area: ['1000px', '430px'],
                    id: 'delRegCode',//配置ID
                    content: "<div class=\"layui-card\">\n" +
                        "    <div class=\"layui-card-body\">\n" +
                        "        <table id=\"doc-table\" lay-filter=\"doc-table\"></table>\n" +
                        "    </div>\n" +
                        "</div>",
                    success: function (index, layero) {
                        let cols = [
                            [
                                {type: 'radio', width: 20},
                                {title: '文档名称', field: 'name', align: 'left', templet: "#doc-name", minWidth: 280},
                                {title: '状态', field: 'status', align: 'left', templet: "#doc-status", width: 90},
                                {title: '已分发平台',field: 'plant_list',align: 'left',templet:"#doc-plant-list"},
                                {title: '文集', field: 'project_name', align: 'left', templet: "#project-role"},
                                {title: '文档作者', field: 'create_user', align: 'left',}
                              ]
                        ]
                        // 渲染表格
                        table.render({
                            elem: '#doc-table',
                            method: 'post',
                            type: 1,
                            url: "{% url 'doc_manage' %}",
                            page: true,
                            cols: cols,
                            skin: 'line',
                            toolbar: '#doc-toolbar',
                            defaultToolbar: ['filter']
                        });
                            table.on('radio(doc-table)', function (obj) {
                            doc_id = obj.data.id;
                            if(plant_name === 'CSDN' || plant_name === '思否' || plant_name === '知乎'){
                                layer.open({
                                    type: 1,
                                    title: '请输入文章标签：',
                                    area: '300px;',
                                    id: 'createRegCode',//配置ID
                                    content: '<div style="margin:10px;"><input class="layui-input" id="tags" type="text" placeholder="请输入文章标签，以英文逗号隔开"/></div>',
                                    btn: ['确定', '取消'], //添加按钮
                                    btnAlign: 'c', //按钮居中
                                    yes: function (index, layero) {
                                        tags = $("#tags").val();
                                        layer.close(index)
                                    },
                                });
                            }else if(plant_name === '博客园'){
                                tags = $("#tags").val();
                        }
                        });

                    },
                    btn: ['确定', '取消'], //添加按钮
                    btnAlign: 'c', //按钮居中

                    yes: function (index, layero) {
                        if (doc_id === '') {
                            layer.msg("请选择需要发布的文章！");
                            return
                        }
                        data = {
                            'types': 3,
                            'doc_id': doc_id,
                            'tags': tags,
                            'code_id': code_id
                        };
                        $.post("{% url 'article_distribution' %}", data, function (r) {
                            if (r.status) {
                                layer.msg(r.data, function () {
                                    window.location.reload();
                                });
                                //删除成功，刷新页面
                                // {#window.location.reload();#}
                                //layer.close(index)
                            } else {
                                //删除失败，提示
                                console.log(r)
                                layer.msg(r.data)
                            }
                        })
                    },
                });
            }
            // 一键分发到所有平台
            onePushAll = function () {
                var doc_id = '';
                var tags = '';
                layer.open({
                    type: 1,
                    title: '文章分发',
                    area: ['1000px', '430px'],
                    id: 'delRegCode',//配置ID
                    content: "<div class=\"layui-card\">\n" +
                        "    <div class=\"layui-card-body\">\n" +
                        "        <table id=\"doc-table\" lay-filter=\"doc-table\"></table>\n" +
                        "    </div>\n" +
                        "</div>",
                    success: function (index, layero) {
                        let cols = [
                            [
                                {type: 'radio', width: 20},
                                {title: '文档名称', field: 'name', align: 'left', templet: "#doc-name", minWidth: 280},
                                {title: '状态', field: 'status', align: 'left', templet: "#doc-status", width: 90},
                                {title: '已分发平台',field: 'plant_list',align: 'left',templet:"#doc-plant-list"},
                                {title: '文集', field: 'project_name', align: 'left', templet: "#project-role"},
                                {title: '文档作者', field: 'create_user', align: 'left',}
                              ]
                        ]
                        // 渲染表格
                        table.render({
                            elem: '#doc-table',
                            method: 'post',
                            type: 1,
                            url: '/manage_doc/',
                            // url: 'doc_manage/',
                            page: true,
                            cols: cols,
                            skin: 'line',
                            toolbar: '#doc-toolbar',
                            defaultToolbar: ['filter']
                        });
                            table.on('radio(doc-table)', function (obj) {
                            doc_id = obj.data.id;
                            layer.open({
                                type: 1,
                                title: '请输入文章标签：',
                                area: '300px;',
                                id: 'createRegCode',//配置ID
                                content: '<div style="margin:10px;"><input class="layui-input" id="tags" type="text" placeholder="请输入文章标签，以英文逗号隔开"/></div>',
                                btn: ['确定', '取消'], //添加按钮
                                btnAlign: 'c', //按钮居中
                                yes: function (index, layero) {
                                    tags = $("#tags").val();
                                    layer.close(index)
                                },
                            });

                        });

                    },
                    btn: ['确定', '取消'], //添加按钮
                    btnAlign: 'c', //按钮居中

                    yes: function (index, layero) {
                        if (doc_id === '') {
                            layer.msg("请选择需要发布的文章！");
                            return
                        }
                        data = {
                            'doc_id': doc_id,
                            'tags': tags
                        }
                        $.post("{% url 'article_all_distribution' %}", data, function (r) {
                            if (r.status) {
                                layer.msg(r.result, function () {
                                    window.location.href='/doc_publish_manage';
                                });
                                //删除成功，刷新页面
                                // {#window.location.reload();#}
                                //layer.close(index)
                            } else {
                                //删除失败，提示
                                console.log(r)
                                layer.msg(r.data)
                            }
                        })
                    },
                });
            }

        })