from django.shortcuts import render,redirect
from django.http import StreamingHttpResponse
from django.utils.encoding import escape_uri_path
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from userapp.models import *
from adminapp.forms import AffairForm
from django.db.models import Q
import pandas as pd
import os, jieba
from string import digits

area_data = {
        '北京': ['北京市','朝阳区', '海淀区', '通州区', '房山区', '丰台区', '昌平区', '大兴区', '顺义区', '西城区', '延庆县', '石景山区', '宣武区', '怀柔区', '崇文区', '密云县',
               '东城区', '门头沟区', '平谷区'],
        '广东':['广东省', '东莞市', '广州市', '中山市', '深圳市', '惠州市', '江门市', '珠海市', '汕头市', '佛山市', '湛江市', '河源市', '肇庆市','潮州市', '清远市', '韶关市', '揭阳市', '阳江市', '云浮市', '茂名市', '梅州市', '汕尾市'],
        '山东':['山东省', '济南市', '青岛市', '临沂市', '济宁市', '菏泽市', '烟台市','泰安市', '淄博市', '潍坊市', '日照市', '威海市', '滨州市', '东营市', '聊城市', '德州市', '莱芜市', '枣庄市'],
        '江苏':['江苏省', '苏州市', '徐州市', '盐城市', '无锡市','南京市', '南通市', '连云港市', '常州市', '扬州市', '镇江市', '淮安市', '泰州市', '宿迁市'],
        '河南':['河南省', '郑州市', '南阳市', '新乡市', '安阳市', '洛阳市', '信阳市','平顶山市', '周口市', '商丘市', '开封市', '焦作市', '驻马店市', '濮阳市', '三门峡市', '漯河市', '许昌市', '鹤壁市', '济源市'],
        '上海':['上海市', '松江区', '宝山区', '金山区','嘉定区', '南汇区', '青浦区', '浦东新区', '奉贤区', '闵行区', '徐汇区', '静安区', '黄浦区', '普陀区', '杨浦区', '虹口区', '闸北区', '长宁区', '崇明县', '卢湾区'],
        '河北':[ '河北省', '石家庄市', '唐山市', '保定市', '邯郸市', '邢台市', '河北区', '沧州市', '秦皇岛市', '张家口市', '衡水市', '廊坊市', '承德市'],
        '浙江':['浙江省', '温州市', '宁波市','杭州市', '台州市', '嘉兴市', '金华市', '湖州市', '绍兴市', '舟山市', '丽水市', '衢州市'],
        '陕西':['陕西省', '西安市', '咸阳市', '宝鸡市', '汉中市', '渭南市','安康市', '榆林市', '商洛市', '延安市', '铜川市'],
        '湖南':[ '湖南省', '长沙市', '邵阳市', '常德市', '衡阳市', '株洲市', '湘潭市', '永州市', '岳阳市', '怀化市', '郴州市','娄底市', '益阳市', '张家界市', '湘西州'],
        '重庆':[  '重庆市', '江北区', '渝北区', '沙坪坝区', '九龙坡区', '万州区', '永川市', '南岸区', '酉阳县', '北碚区', '涪陵区', '秀山县', '巴南区', '渝中区', '石柱县', '忠县', '合川市', '大渡口区', '开县', '长寿区', '荣昌县', '云阳县', '梁平县', '潼南县', '江津市', '彭水县', '璧山县', '綦江县',
     '大足县', '黔江区', '巫溪县', '巫山县', '垫江县', '丰都县', '武隆县', '万盛区', '铜梁县', '南川市', '奉节县', '双桥区', '城口县'],
        '福建':['福建省', '漳州市', '泉州市','厦门市', '福州市', '莆田市', '宁德市', '三明市', '南平市', '龙岩市'],
        '天津':['天津市', '和平区', '北辰区', '河北区', '河西区', '西青区', '津南区', '东丽区', '武清区','宝坻区', '红桥区', '大港区', '汉沽区', '静海县', '宁河县', '塘沽区', '蓟县', '南开区', '河东区'],
        '云南':[ '云南省', '昆明市', '红河州', '大理州', '文山州', '德宏州', '曲靖市', '昭通市', '楚雄州', '保山市', '玉溪市', '丽江地区', '临沧地区', '思茅地区', '西双版纳州', '怒江州', '迪庆州'],
        '四川':['四川省', '成都市', '绵阳市', '广元市','达州市', '南充市', '德阳市', '广安市', '阿坝州', '巴中市', '遂宁市', '内江市', '凉山州', '攀枝花市', '乐山市', '自贡市', '泸州市', '雅安市', '宜宾市', '资阳市','眉山市', '甘孜州'],
        '广西':['广西壮族自治区', '贵港市', '玉林市', '北海市', '南宁市', '柳州市', '桂林市', '梧州市', '钦州市', '来宾市', '河池市', '百色市', '贺州市', '崇左市',  '防城港市'],
        '安徽':['安徽省', '芜湖市', '合肥市', '六安市', '宿州市', '阜阳市','安庆市', '马鞍山市', '蚌埠市', '淮北市', '淮南市', '宣城市', '黄山市', '铜陵市', '亳州市','池州市', '巢湖市', '滁州市'],
        '海南':['海南省', '三亚市', '海口市', '琼海市', '文昌市', '东方市', '昌江县', '陵水县', '乐东县', '五指山市', '保亭县', '澄迈县', '万宁市','儋州市', '临高县', '白沙县', '定安县', '琼中县', '屯昌县'],
        '江西':['江西省', '南昌市', '赣州市', '上饶市', '吉安市', '九江市', '新余市', '抚州市', '宜春市', '景德镇市', '萍乡市', '鹰潭市'],
        '湖北':['湖北省', '武汉市', '宜昌市', '襄樊市', '荆州市', '恩施州', '孝感市', '黄冈市', '十堰市', '咸宁市', '黄石市', '仙桃市', '随州市', '天门市', '荆门市', '潜江市', '鄂州市', '神农架林区'],
        '山西':['山西省', '太原市', '大同市', '运城市', '长治市', '晋城市', '忻州市', '临汾市', '吕梁市', '晋中市', '阳泉市', '朔州市'],
        '辽宁':['辽宁省', '大连市', '沈阳市', '丹东市', '辽阳市', '葫芦岛市', '锦州市', '朝阳市', '营口市', '鞍山市', '抚顺市', '阜新市', '本溪市', '盘锦市', '铁岭市'],
        '台湾':['台湾省','台北市', '高雄市', '台中市', '新竹市', '基隆市', '台南市', '嘉义市'],
        '黑龙江':['黑龙江', '齐齐哈尔市', '哈尔滨市', '大庆市', '佳木斯市', '双鸭山市', '牡丹江市', '鸡西市','黑河市', '绥化市', '鹤岗市', '伊春市', '大兴安岭地区', '七台河市'],
        '内蒙古':['内蒙古自治区', '赤峰市', '包头市', '通辽市', '呼和浩特市', '乌海市', '鄂尔多斯市', '呼伦贝尔市','兴安盟', '巴彦淖尔盟', '乌兰察布盟', '锡林郭勒盟', '阿拉善盟'],
        '香港':["香港","香港特别行政区"],
        '澳门':['澳门','澳门特别行政区'],
        '贵州':['贵州省', '贵阳市', '黔东南州', '黔南州', '遵义市', '黔西南州', '毕节地区', '铜仁地区','安顺市', '六盘水市'],
        '甘肃':['甘肃省', '兰州市', '天水市', '庆阳市', '武威市', '酒泉市', '张掖市', '陇南地区', '白银市', '定西地区', '平凉市', '嘉峪关市', '临夏回族自治州','金昌市', '甘南州'],
        '青海':['青海省', '西宁市', '海西州', '海东地区', '海北州', '果洛州', '玉树州', '黄南藏族自治州'],
        '新疆':['新疆','新疆维吾尔自治区', '乌鲁木齐市', '伊犁州', '昌吉州','石河子市', '哈密地区', '阿克苏地区', '巴音郭楞州', '喀什地区', '塔城地区', '克拉玛依市', '和田地区', '阿勒泰州', '吐鲁番地区', '阿拉尔市', '博尔塔拉州', '五家渠市',
     '克孜勒苏州', '图木舒克市'],
        '西藏':['西藏区', '拉萨市', '山南地区', '林芝地区', '日喀则地区', '阿里地区', '昌都地区', '那曲地区'],
        '吉林':['吉林省', '吉林市', '长春市', '白山市', '白城市','延边州', '松原市', '辽源市', '通化市', '四平市'],
        '宁夏':['宁夏回族自治区', '银川市', '吴忠市', '中卫市', '石嘴山市', '固原市']
}

# 根据城市返回省份
def get_province_name(city):
    for k, v in area_data.items():
        for i in v:
            if city in i:
                return k
    return None

# 首页
def index(request):
    # 获取全部数据将数据转化为pandas可以处理的格式DataFrame
    res = Affair.objects.all()
    df = pd.DataFrame(res.values())

    # 折线图
    # 缺失值处理，将时间为空值的行删除，并使删除的结果生效
    df.dropna(subset=['Time'], inplace=True)
    # 时间值保留日期
    df['Time'] = pd.to_datetime(df['Time']).dt.to_period('M')
    # 获取数据中有哪些城市
    citys_data = df.groupby(by='City')  # 将数据按城市分组,以列表形式输出
    citys = list(citys_data.groups.keys())
    # 获取数据中有哪些月份
    mouth = df.groupby(by='Time').groups.keys()  # 将数据按月份分组
    dates = []  # 以列表形式输出
    for i in mouth:
        dates.append(str(i))
    # 统计每个城市，各个月份的数据数量
    datas = []
    this_mouth = 0 # 本月数据
    last_mouth = 0 # 上月数据
    for i in citys:
        data = []
        for j in mouth:
            try:
                data.append(int(df[(df['City'] == i) & (df['Time'] == j)].groupby('Time')['id'].count()))
            except:
                data.append(0)
        datas.append({
            'name': i,
            'data': data
        })
        this_mouth = this_mouth+data[-1]
        last_mouth = last_mouth+data[-2]

    # 地图
    citys_count = dict(citys_data['Title'].count()) # 统计每个城市的政务数据数量
    map_res = {}
    for i in citys_count:
        # 获取省份
        province = get_province_name(i)
        if province:
            if province in map_res:  # 同省份城市数据相加
                map_res[province] = map_res[province] + citys_count[i]
            else:
                map_res[province] = citys_count[i]
    # 地图数据
    map = []
    for i in area_data:
        if i in map_res:
            map.append({'value': map_res[i], 'name': i})
        else:
            map.append({'value': 0, 'name': i})

    # 增长幅度=增幅=增长率＝（本期数-上期数）/上期数*100％
    raise_rate = round((this_mouth-last_mouth) /last_mouth * 100,2)
    res = {
        'total': df['id'].count(),
        'raise_rate':raise_rate,
        'city_count':len(datas),
        'this_mouth':this_mouth,
        'datas':datas,
        'dates':dates,
        'citys':citys,
        'map':map,
    }
    return render(request, 'user/index.html', res)


def register(request):
    '''注册'''
    if request.method == 'GET':
        '''显示注册页面'''
        return render(request, 'register.html')
    if request.method == 'POST':
        '''进行注册处理'''
        # 接收数据
        username = request.POST.get('username')
        pwd = request.POST.get('password')

        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None
        if user:
            # 用户名已存在
            return render(request, 'register.html', {'errmsg': '用户名已存在'})

        # 创建账户
        account = User.objects.create_user(username=username, password=pwd)
        # 自动激活用户
        account.is_active = 1
        account.save()

        role = request.POST.get('role')
        if role == '管理员':  # 如果注册角色为管理员, 则该用户设置为管理员身份
            # 账户设置为管理员
            account.is_superuser = 1
            account.save()
        # 返回应答, 跳转到登录页面
        return redirect('/login/')
# 登录
def login_(request):
    if request.method == 'GET':
        return render(request, 'login.html')

    elif request.method == 'POST':
        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 校验数据
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '请将必填项填写完整'})

        # 业务处理:登录校验
        user = authenticate(username=username, password=password)
        if user is not None:
            # 用户名密码正确
            login(request, user)
            if user.is_superuser:
                return redirect('/admin/')
            else:
                return redirect('/')
        else:
            # 用户名或密码错误
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})

# 退出登录
@login_required
def logout_(request):
    logout(request)  # 清除用户的session信息
    return redirect('/login/')


# 数据查询
@login_required
def showdata(request):
    if request.user.is_superuser: # 验证用户身份，不是用户则跳转到登陆页面
        return redirect('/login/')
    lists = Affair.objects.all()
    # 搜索
    search = request.GET.get('search','')
    if search:
        lists = lists.filter(Q(City__icontains=search)|Q(Title__icontains=search))

    paginator = Paginator(lists, 10)
    page = request.GET.get('page')
    try:
        contacts = paginator.page(page)
    except PageNotAnInteger:
        contacts = paginator.page(1)
    except EmptyPage:
        contacts = paginator.page(paginator.num_pages)
    return render(request, 'user/showdata.html', {'search':search,'contacts':contacts,'page':page})


# 详情页
@login_required
def detail(request, id):
    if request.user.is_superuser: # 验证用户身份，不是用户则跳转到登陆页面
        return redirect('/login/')
    # 根据类型获取数据
    info = Affair.objects.get(id=id)
    form = AffairForm(instance=info)
    return render(request, 'user/detail.html', locals())


def file_iterator(filename, chunk_size=512):
    with open(filename, 'rb') as f:
        while True:
            c = f.read(chunk_size)
            if c:
                yield c
            else:
                break

# 数据下载:显示数据下载页面
@login_required
def download(request):
    if request.user.is_superuser: # 验证用户身份，不是用户则跳转到登陆页面
        return redirect('/login/')
    # 获取数据中有哪些城市
    df = pd.DataFrame(Affair.objects.all().values())
    citys = list(df.groupby(by='City').groups.keys()) # 将数据按城市分组,以列表形式输出
    return render(request, 'user/download.html',{'citys':citys})


# 数据下载:向前台提交一个数据文件
def getdata(request):
    if request.user.is_superuser: # 验证用户身份，不是用户则跳转到登陆页面
        return redirect('/login/')
    city = request.POST.get('city', '')
    res = Affair.objects.all().filter(City=city)
    info = res.values('City', 'Title', 'Time', 'Content', 'RepDep', 'RepTime', 'RepCon', 'URL')
    if len(info) > 0:
        df = pd.DataFrame.from_records(info)
        writer = pd.ExcelWriter('data.xlsx')
        df.to_excel(writer, sheet_name='认证信息', index=False)
        writer.close()
        file = '政务信息-' + city + '.xlsx'
        response = StreamingHttpResponse(file_iterator('data.xlsx'))
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment; filename="{}" '.format(escape_uri_path(file))
        return response

# 词云
def wordcloud(projects):
    # 获取所有标题
    yd_ls = []
    for p in projects:
        # 获取标题内容
        content = p.Title
        # 删除标题中数字
        remove_digits = str.maketrans('', '', digits)
        content = content.translate(remove_digits)
        # 将标题存入列表
        yd_ls.append(content)

    # 把所有标题合并成一个字符串
    temp1 = " ".join(yd_ls)

    # 载入停止词，进行文本数据清洗，除去不必要的标点、感叹词、代词等
    stopwords = [line.strip() for line in open(os.getcwd() + "/cnstopwords.txt", encoding='utf-8').readlines()]
    # 用jieba进行分词，将整个字符串分成一个一个词语
    sentence_depart1 = jieba.lcut(temp1.strip())

    # 获取字典，统计词频，每个词出现了几次
    worddic1 = {}
    for word in sentence_depart1:
        if word != ' ':
            if word not in stopwords:
                worddic1[word] = worddic1.get(word, 0) + 1

    # 返回词频统计结果
    return worddic1

#
@login_required
def charts(request):
    if request.user.is_superuser: # 验证用户身份，不是用户则跳转到登陆页面
        return redirect('/login/')
    # 获取全部数据将数据转化为pandas可以处理的格式DataFrame
    res = Affair.objects.all()
    df = pd.DataFrame(res.values())
    print(df.info())
    # 缺失值处理，将时间为空值的行删除，并使删除的结果生效
    df.dropna(subset=['Time'],inplace=True)
    # 时间值保留日期
    df['Time'] = pd.to_datetime(df['Time']).dt.to_period('M')
    # 获取数据中有哪些城市
    citys = list(df.groupby(by='City').groups.keys()) # 将数据按城市分组,以列表形式输出
    # 获取数据中有哪些月份
    mouth = df.groupby(by='Time').groups.keys()  # 将数据按月份分组
    dates = []  # 以列表形式输出
    for i in mouth:
        dates.append(str(i))
    # 统计每个城市，各个月份的数据数量
    datas = []
    for i in citys:
        data = []
        for j in mouth:
            try:
                data.append(int(df[(df['City']==i)&(df['Time']==j)].groupby('Time')['id'].count()))
            except:
                data.append(0)
        datas.append({
            'name': i,
            'data': data
        })

    worddic = wordcloud(res) # 获取词频统计
    return render(request, 'user/charts.html', {'citys':citys,'dates':dates,'datas':datas,'worddic':worddic})