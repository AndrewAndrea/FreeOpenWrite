/*
    ########################################################
    ### 文集、文档等前台浏览页面通用JavaScript函数和变量定义 ###
    ########################################################
*/

// Ajax默认配置
$.ajaxSetup({
    data: {csrfmiddlewaretoken: '{{ csrf_token }}' },
});

// 视频iframe域名白名单
var iframe_whitelist = '{{ iframe_whitelist }}'.split(',')

//为当前页面的目录链接添加蓝色样式
tagCurrentDoc = function(){
    $("nav li a").each(function (i) {
        var $me = $(this);
        var lochref = $.trim(window.location.href); // 获取当前URL
        var mehref = $.trim($me.get(0).href); 
        if (lochref.indexOf(mehref) != -1) {
            // console.log($me,lochref,mehref)
            $me.closest("li").addClass("active");
            // 展开当前文档的下级目录
            if($me.parent().next("ul.sub-menu").hasClass("toc-close")){
                // console.log("展开下级目录")
                $me.parent().next("ul.sub-menu").toggleClass("toc-close");
                $me.next("i").toggleClass("layui-icon-left layui-icon-down");
            }
            // 展开当前文档的所有上级目录
            if($me.parent("li").parent('ul.sub-menu').hasClass("toc-close")){
                // console.log("展开二级文档目录")
                $me.parent("li").parent('ul.sub-menu').toggleClass("toc-close");
            }
            if($me.parent("div").parent('li').parent('ul.sub-menu').hasClass("toc-close")){
                // console.log("展开包含下级的二级文档目录")
                $me.parent("div").parent('li').parent('ul.sub-menu').toggleClass("toc-close");
            }
            if($me.parent("li").parent('ul').parent('li').parent('ul.sub-menu').hasClass("toc-close")){
                // console.log("展开三级目录")
                $me.parent("li").parent('ul').parent('li').parent('ul.sub-menu').toggleClass("toc-close");
            }
            // 切换图标
            $me.parents("ul.sub-menu").prevAll("div").each(function(i){
                var $link = $(this);
                if($link.children("i").hasClass("layui-icon-left")){
                    $link.children("i").toggleClass("layui-icon-left layui-icon-down");
                }
            })
            // 目录的当前文档滚动于目录顶端
            this.scrollIntoView({ behavior: 'auto', block: "start" });
        } else {
            // console.log(lochref,mehref)
            $me.closest("li").removeClass("active");
        }
    });
};
tagCurrentDoc();

/*
    小屏幕下的文集大纲显示处理
*/
//监听浏览器宽度的改变
window.onresize = function(){
    changeSidebar();
};
function changeSidebar(){
    // 获取匹配指定的媒体查询
    var screen_width = window.matchMedia('(max-width: 768px)');
    //判断匹配状态
    if(screen_width.matches){
        //如果匹配到，切换侧边栏
        console.log('小屏幕')
        $("body").addClass("big-page");
    }else{
        $("body").removeClass("big-page");
    }
};
// 监听文档div点击
document.querySelector('.doc-body').addEventListener('click', function (e) {
    var screen_width = window.matchMedia('(max-width: 768px)');
    // 小屏下收起左侧文集大纲
    if(screen_width.matches){
        // console.log("点击了div")
        changeSidebar();
    }
});

/* 
    切换隐藏侧边栏
*/
// 初始化左侧文集大纲状态
function init_sidebar(){
    var screen_width = window.matchMedia('(max-width: 768px)');
    if(screen_width.matches){}else{
        // 读取浏览器存储
        bgpage_status = window.localStorage.getItem('bgpage')
        console.log("左侧大纲状态：",bgpage_status)
        if(bgpage_status === null){ // 如果没有值，则默认展开
            $("body").toggleClass("big-page");
        }else if(bgpage_status === '1'){ // 如果值为1，则默认展开
            if($("body").hasClass("big-page")){}else{
                $("body").toggleClass("big-page");
            }
        }
        else{ // 否则收起
            if($("body").hasClass("big-page")){
                $("body").toggleClass("big-page");
            }else{
                window.localStorage.setItem('bgpage','0')
            }
            
        }
    }
    
}
init_sidebar();
// 切换侧边栏
$(function(){
    $(".js-toolbar-action").click(toggleSidebar);
});
//切换侧边栏显示隐藏
function toggleSidebar(){
    console.log("切换侧边栏")
    $("body").toggleClass("big-page");
    if(window.localStorage.getItem('bgpage') === '1'){
        window.localStorage.setItem('bgpage','0')
    }else{
        window.localStorage.setItem('bgpage','1')
    }
    return false;
}

/*
    页面初始化字体设置
*/
font_stauts = window.localStorage.getItem('font-sans')
if(font_stauts == 'serif'){// 字体类型
    $(".doc-content").toggleClass("switch-font")
    $("#content").toggleClass("switch-font")
}
if(window.localStorage.getItem('font-size')){// 字体大小
    font_size = window.localStorage.getItem('font-size')
    console.log(font_size)
    $('#content').css({'font-size':font_size+'rem'})
}else{
    window.localStorage.setItem('font-size',1.0)
}

/*
    返回顶部
*/
$(document).ready(function() {
    // 初始时，“返回顶部”标签隐藏
    $(".toTop").hide();
    $(".editDoc").hide();
    $(window).scroll(function() {
        // 若滚动的高度，超出指定的高度后，“返回顶部”的标签出现。
        if($(document).scrollTop() >= 140) {
            $(".toTop").show();
            $(".editDoc").show();
        } else {
            $(".toTop").hide();
            $(".editDoc").hide();
        }
    })
    // 绑定点击事件，实现返回顶部的效果
    $(".toTop").click(function() {
        $(document).scrollTop(0);
    });
    // 生成当前网页链接
    $("input[name=current_url]").val(document.URL)
});

/*
    切换字体类型
*/
$(function(){
    $('.font-switch').click(switchFont);
});
//切换文档内容字体类型
function switchFont(){
    if(font_stauts == 'serif'){
        $(".doc-content").toggleClass("switch-font")
        $("#content").toggleClass("switch-font")
        window.localStorage.setItem('font-sans','sans')
    }else{
        $(".doc-content").toggleClass("switch-font")
        $("#content").toggleClass("switch-font")
        window.localStorage.setItem('font-sans','serif')
    }
};
//放大字体
$(function(){
    $('.font-large').click(largeFont);
});
function largeFont(){
    var font_size = window.localStorage.getItem('font-size')
    console.log(font_size)
    if(parseFloat(font_size) < 1.4){
        size = parseFloat(font_size) + 0.1
        $('#content').css({'font-size':size+'rem'})
        window.localStorage.setItem('font-size',size)
    }else{
        console.log("xxx")
    }
};
//缩小字体
$(function(){
    $('.font-small').click(smallFont);
});
function smallFont(){
    var font_size = window.localStorage.getItem('font-size')
    if(parseFloat(font_size) >= 0.6){
        size = parseFloat(font_size) - 0.1
        $('#content').css({'font-size':size+'rem'})
        window.localStorage.setItem('font-size',size)
    }else{
        console.log("xxx")
    }
};

/*
    显示打赏图片
*/
$("#dashang").click(function(r){
    var layer = layui.layer;
    layer.open({
        type: 1,
        title: false,
        closeBtn: 0,
        area: ['480px','400px'],
        shadeClose: true,
        content: $('#dashang_img')
      });
});

/*
    右侧文档目录
*/
$(function(){
    // $(".switch-toc").click(SwitchToc);
    $("body").on('click','.switch-toc',SwitchToc);
});
// 切换文档目录
function SwitchToc(i){
    // console.log("点击了")
    var $me = $(this);
    $(this).parent().next("ul").toggleClass("toc-close"); //切换展开收起样式
    $(this).toggleClass("layui-icon-left layui-icon-down");//切换图标
};

// $(".switch-toc-div").click(function(e){
//     console.log(e)
//     $(this).children("i").trigger('click')
// });

// 展开文档树
function openDocTree(){
    $("nav ul.summary ul").each(function(obj){
        console.log(obj,this)
        $(this).removeClass("toc-close")
        $(this).prev().children('i').toggleClass("layui-icon-left layui-icon-down");//切换图标
    })
    
};
// 收起文档树
function closeDocTree(){
    $("nav ul.summary ul").each(function(obj){
        console.log(obj,this)
        $(this).addClass("toc-close")
        $(this).prev().children('i').toggleClass("layui-icon-left layui-icon-down");//切换图标
    })
};

/*
    文档分享
*/
// 显示分享弹出框
$("#share").click(function(r){
    var layer = layui.layer;
    layer.open({
        type: 1,
        title: false,
        closeBtn: 0,
        area: ['350px','350px'],
        shadeClose: true,
        content: $('#share_div')
      });
});
// 复制文档链接
copyUrl = function(){
    var crt_url_val = document.getElementById("copy_crt_url");
    crt_url_val.select();
    window.clipb
    document.execCommand("Copy");
    layer.msg("链接复制成功！")
}
$("#copy_doc_url").click(function(){
    copyUrl();
})
// 生成文档链接二维码
doc_qrcode = function(){
    new QRCode("url_qrcode", {
        text: document.URL,
        width: 200,
        height: 200,
        colorDark : "#000000",
        colorLight : "#ffffff",
        correctLevel : QRCode.CorrectLevel.H
    });
};
doc_qrcode();

// 文集水印
textBecomeImg = function(text,fontsize,fontcolor){
    var canvas = document.createElement('canvas');
    canvas.height = 180;
    canvas.width = 400;
    var context = canvas.getContext('2d');
    // 擦除(0,0)位置大小为200x200的矩形，擦除的意思是把该区域变为透明
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = fontcolor;
    context.font=fontsize+"px Arial";
    context.rotate(-25 * Math.PI / 180)
    context.fillText(text,10,160);
    
    var dataUrl = canvas.toDataURL('image/png');//注意这里背景透明的话，需要使用png
    return dataUrl;
}
/*
    ########################################################
    ### 文集阅读页面JavaScript函数和变量定义 ###
    ########################################################
*/



/*
    ########################################################
    ### 文档阅读页面JavaScript函数和变量定义 ###
    ########################################################
*/

    // URL参数解析
    function getQueryVariable(variable)
    {
        var query = window.location.search.substring(1);
        var vars = query.split("&");
        for (var i=0;i<vars.length;i++) {
                var pair = vars[i].split("=");
                if(pair[0] == variable){return pair[1];}
        }
        return(false);
    }

    // 搜索词高亮
    function keyLight(id, key, bgColor){
        // console.log(id,key,decodeURI(key))
        key = decodeURI(key);
        var oDiv = document.getElementById(id),
        sText = oDiv.innerHTML,
        bgColor = bgColor || "#c00",    
        sKey = "<span name='addSpan' style='color: "+bgColor+";background:ff0;'>"+key+"</span>",
        num = -1,
        rStr = new RegExp(key, "ig"),
        rHtml = new RegExp("\<.*?\>","ig"), //匹配html元素
        aHtml = sText.match(rHtml); //存放html元素的数组
        sText = sText.replace(rHtml, '{~}');  //替换html标签
        // sText = sText.replace(rStr,sKey); //替换key
        sText = sText.replace(rStr,function(text){
            return "<span name='addSpan' style='color:#333;background:#ff0;'>"+text+"</span>"
        }); //替换key
        sText = sText.replace(/{~}/g,function(){  //恢复html标签
                num++;
                return aHtml[num];
        });
        oDiv.innerHTML = sText;
    };
    keyLight('doc-content',getQueryVariable("highlight"))