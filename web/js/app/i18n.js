// 九州 UI 本地化层：把上游英文界面逐词替换为中文，不改变数据与交互。
// 采用 MutationObserver 处理动态生成的 DOM 文本与 title/aria 属性；数据里的中文名称不受影响。
const DICT = new Map(Object.entries({
  // global chrome
  "Share": "分享", "Almanac": "图鉴", "Advisors": "顾问团", "Search": "搜索", "Map": "地图", "Resources": "资源",
  "Terrain": "地形", "Lenses": "镜头", "Population": "人口", "Unemployment": "失业率", "Unemployment rate": "失业率",
  "Open the report": "打开报告", "Close": "关闭", "Close panel (Esc)": "关闭面板（Esc）",
  "Keyboard and mouse help": "键盘与鼠标帮助", "Open the Almanac": "打开图鉴", "Share this view": "分享此视图",
  "Map layers": "地图图层", "Minimap: click to jump": "缩略图：点击跳转",
  // quick city panel
  "OPEN CITY VIEW": "进入城市视图", "Open City View": "进入城市视图",
  "YIELDS": "产出", "AMENITIES & HOUSING": "民生与住房", "DISTRICTS · WHERE PEOPLE WORK": "城区 · 就业分布",
  "DISTRICTS": "城区", "Districts": "城区", "DISTRICTS ›": "城区 ›",
  "Almanac ›": "图鉴 ›", "people": "人", "employed": "就业", "since": "较",
  "Median household income": "居民可支配收入", "Median home value": "住房总价",
  "Median gross rent / mo": "月租金", "Rent ÷ income": "租金收入比", "per person": "人均",
  "State": "省份", "City": "城市", "County": "区县", "Metro": "城市",
  // city view header
  "City View · Metropolitan area": "城市视图 · 地级市", "City View · Micropolitan area": "城市视图 · 县级市",
  "CITY VIEW · METROPOLITAN AREA": "城市视图 · 地级市", "CITY VIEW · MICROPOLITAN AREA": "城市视图 · 县级市",
  "POPULATION": "人口", "GDP / PERSON": "人均 GDP", "GROWTH": "增长",
  "Population": "人口", "GDP": "GDP", "GDP per person": "人均 GDP", "Growth": "增长",
  // city view tabs
  "CITIZENS": "市民", "ECONOMY": "经济", "WORKFORCE": "劳动力", "COMPARE": "对比",
  "Citizens": "市民", "Economy": "经济", "Workforce": "劳动力", "Compare": "对比",
  // citizens
  "MEDIAN AGE": "年龄中位数", "HAVE A DEGREE": "大专以上", "BORN ABROAD": "境外出生",
  "Median age": "年龄中位数", "have a degree": "大专以上", "born abroad": "境外出生",
  "WORKFORCE": "劳动力", "by occupation": "职业构成", "GENERATIONS": "代际", "by age": "年龄结构",
  "COMMUTE": "通勤", "how workers get to work": "通勤方式", "EDUCATION": "教育", "adults 25 and over": "25 岁以上",
  "ORIGINS": "出生地", "where residents were born": "出生地构成",
  "Under 18": "18 岁以下", "18–34": "18–34 岁", "35–64": "35–64 岁", "65+": "65 岁以上",
  "Executives": "管理者", "Engineers": "工程师", "Teachers & arts": "教师与文艺", "Health": "医护",
  "Service": "服务业", "Sales & office": "销售与职员", "Farm": "农业", "Builders": "建筑工", "Makers & movers": "产业工人",
  "Drive alone": "自驾", "Carpool": "拼车", "Transit": "公共交通", "Walk": "步行", "Bike & other": "骑行等", "From home": "居家",
  "No diploma": "初中及以下", "High school": "高中", "Some college": "大专", "Bachelor's": "本科", "Graduate": "研究生",
  "This state": "本省", "Other state": "外省", "U.S. citizen abroad": "境外出生", "Other country": "外籍",
  "US": "全国", "U.S.": "全国", "in the U.S.": "全国",
  "Member counties": "下辖区县", "Loading counties…": "正在载入区县…", "County table not available.": "无区县表。",
  "People": "人口", "Income": "收入", "/km²": "人/km²",
  "No county rows for this metro.": "该城市没有区县数据。",
  // city view sections
  "Citizens": "市民", "Population change": "人口变化", "Census population estimates": "人口普查估计",
  "Employed residents": "就业人口", "Rent burden (rent ÷ income)": "租金收入比",
  "Districts · where people work": "城区 · 就业分布",
  // districts
  "Districts": "城区", "The metro's specialised districts": "城市的特色城区",
  "Campus": "学府区", "Commercial hub": "商务中心", "Industrial zone": "工业区", "Harbor": "港口",
  "Theater square": "文化广场", "Entertainment complex": "休闲区", "Aerodrome": "航空港",
  "Government plaza": "政务区", "Encampment": "驻防", "Aqueduct & dam": "水利枢纽",
  "Knowledge city": "科技城", "Finance city": "金融城", "Factory town": "制造之都", "Port city": "港城",
  "Arts city": "文化名城", "Resort city": "休闲之城", "Air hub": "航空枢纽", "Government town": "政治中心",
  // advisors
  "Energy & Resources": "能源与资源", "Minister of Power": "能源大臣", "Economy": "经济", "Treasurer": "财政大臣",
  "People": "人口", "Keeper of the Census": "户部尚书", "Prosperity & Housing": "民生与住房", "Steward of the Hearth": "民生大臣",
  "Knowledge": "科教", "Royal Scholar": "翰林学士", "Land": "土地", "Surveyor General": "舆图总办",
  "Military": "国防", "General": "将军", "Commerce": "商贸", "Master of Trade": "市舶使",
  "Culture": "文化", "Keeper of Wonders": "奇观守护者", "Explorer": "探索器", "Cartographer": "制图师",
  // tables and controls
  "Search sites, states, operators": "搜索站点、省份、运营方", "Search metros": "搜索城市", "Search": "搜索",
  "All": "全部", "None": "无", "Other": "其他", "Type": "类型", "Site": "站点", "Size": "规模",
  "Sort by capacity (MW; other units sort last)": "按装机排序（MW，其他单位排在最后）",
  "Show GDP circles": "显示 GDP 圆点", "Show roads, rail and forts": "显示道路、铁路与驻防",
  "Clear": "清除", "Show all": "显示全部",
  "Generations": "代际", "GDP / person": "人均 GDP", "City View:": "城市视图：",
  "Map layers (4 of 4 on)": "地图图层（4/4 开启）", "City View": "城市视图",
  "GDP / PERSON": "人均 GDP", "GROWTH": "增长",

  // 补充
  'District positions are schematic': '城区位置为示意',
  'residents per hex': '每格人口',
  'main land use': '主要用地',
  'districts: real specialisations': '城区：真实产业特色',
  'Share of U.S. GDP': '占全国 GDP',
  'of people': '人口占比',
  'Median rent / month': '月租金',
  'ACS 1-year': '全国 1 年调查',
  'Empty': '无数据',
  'No data': '无数据',
  'Population density': '人口密度',
  'Close help': '关闭帮助',
  'How districts are chosen': '城区如何选出',
  'Strongest speciality': '最强细分',
  'Qualifies through': '通过细分行业入选',
  'Above norm': '高于全国',
  'Avg pay': '平均工资',
  'Jobs': '就业',
  'Pay': '工资',
  'Industry': '行业',
  'Search results': '搜索结果',
  'Choose a lens': '选择镜头',
  'Map key': '地图图例',
}));


// 顾问看板的高频标签
DICT.set('Per person', '人均');
DICT.set('Top industry', '最大行业');
DICT.set('current dollars', '现价人民币');
DICT.set('United States', '全国');
DICT.set('GDP by industry', '分行业 GDP');
DICT.set('Metro economies on the map', '地图上的城市经济');
DICT.set('Leading metros', '领先城市');
DICT.set('Rank by', '排序');
DICT.set('Largest GDP', 'GDP 最大');
DICT.set('GDP per person', '人均 GDP');
DICT.set('Fastest growing', '增长最快');
DICT.set('Metro', '城市');
DICT.set('Share of jobs', '就业份额');
DICT.set('Workers', '就业人数');
DICT.set('Who specialises in what', '谁更专业化');
DICT.set('Power plants', '电厂');
DICT.set('Hydro', '水电');
DICT.set('Wind, solar & batteries', '风电、光伏与储能');
DICT.set('Mines', '矿山');
DICT.set('Oil & gas plays', '油气田');
DICT.set('Mapped power', '已标装机');
DICT.set('Shale plays', '油气田');
DICT.set('The national power mix', '全国电力结构');
DICT.set('Filter the map', '筛选地图');
DICT.set('Resource types', '资源类型');
DICT.set('Sites', '站点');
DICT.set('Site', '站点');
DICT.set('Type', '类型');
DICT.set('State', '省份');
DICT.set('Size', '规模');
DICT.set('Power by state', '分省装机');
DICT.set('What the symbols mean', '符号说明');
DICT.set('Domestic freight', '国内货运');
DICT.set('Busiest port', '最忙港口');
DICT.set('Busiest airport', '最忙机场');
DICT.set('Trade routes', '货运路线');
DICT.set('Value', '价值');
DICT.set('Weight', '重量');
DICT.set('Distance', '距离');
DICT.set('Freight zones', '货运区');
DICT.set('Zone', '区域');
DICT.set('Within', '区内');
DICT.set('Freight that starts and ends inside the zone', '起点和终点都在区内的货运');
DICT.set('To & from zones', '进出其他区');
DICT.set('Imports + exports', '进口 + 出口');
DICT.set('Ports', '港口');
DICT.set('Domestic', '国内');
DICT.set('Imports', '进口');
DICT.set('Exports', '出口');
DICT.set('Airports', '机场');
DICT.set('Passengers', '旅客');
DICT.set('Nature', '自然');
DICT.set('Universities', '大学');
DICT.set('Landmarks', '地标');
DICT.set('Wonders', '奇观');
DICT.set('Park visits', '景区接待');
DICT.set('$1B+ disasters', '十亿美元级灾害');
DICT.set('Adherents ≈', '信教人口 ≈');
DICT.set('Terrain', '地形');
DICT.set('Faith', '信仰');
DICT.set('Tradition', '传统');
DICT.set('Amenities', '生活便利');
DICT.set('Disasters', '灾害');
DICT.set('Kind', '类型');
DICT.set('All', '全部');
DICT.set('Order', '排序');
DICT.set('Most', '最多');
DICT.set('Fewest', '最少');
DICT.set('Amenities and wellbeing', '生活便利与福祉');
DICT.set('Science workers', '科技工作者');
DICT.set('Degree holders', '大专以上人口');
DICT.set('Broadband', '宽带');
DICT.set('Degrees', '学历');
DICT.set('Science jobs', '科技岗位');
DICT.set('The Science yield', '科技产出');
DICT.set('Most workers', '就业最多');
DICT.set('Degrees and income', '学历与收入');
DICT.set('Places', '地区');
DICT.set('Counties', '区县');
DICT.set('Metros', '城市');
DICT.set('Adults with a degree', '大专以上成年人');
DICT.set('Median household income', '居民可支配收入');
DICT.set('Households with broadband', '宽带家庭');
DICT.set('Who is offline', '谁还没上网');
DICT.set('Forest', '森林');
DICT.set('Farmland', '耕地');
DICT.set('Built-up', '建设用地');
DICT.set('What covers the country', '大地被什么覆盖');
DICT.set('Other (barren rock, sand, ice)', '其他（裸岩、沙地、冰雪）');
DICT.set("The states' make-up", '各省土地构成');
DICT.set('Land', '土地');
DICT.set('Largest', '最大');
DICT.set('Sort by', '排序');
DICT.set('Show as', '显示为');
DICT.set('Table', '表格');
DICT.set('Grid', '网格');
DICT.set('Who works the land', '谁在土地上劳作');
DICT.set('Areas', '地区');
DICT.set('States', '省份');
DICT.set('Residents', '居民');
DICT.set('Metros & micros', '城市');
DICT.set('Growth', '增长');
DICT.set('Who is growing, who is shrinking', '谁在增长，谁在收缩');
DICT.set('How crowded', '有多拥挤');
DICT.set('Count', '数量');
DICT.set('People', '人口');
DICT.set('Histogram of county population density', '区县人口密度分布');
DICT.set('Lower-48 average', '全国平均');
DICT.set('Age and immigration', '年龄与迁移');
DICT.set('Median age', '年龄中位数');
DICT.set('Born abroad', '境外出生');
DICT.set('Population', '人口');
DICT.set('median county', '区县中位数');
DICT.set('People per km²', '人/平方公里');
DICT.set('Median income', '收入中位数');
DICT.set('Median home', '住房中位价');
DICT.set('Unemployment', '失业率');
DICT.set('What a home costs', '住房成本');
DICT.set('Median home value', '住房总价');
DICT.set('Home value ÷ income', '房价收入比');
DICT.set('Place', '地区');
DICT.set('Income', '收入');
DICT.set('Home', '住房');
DICT.set('Ratio', '比值');
DICT.set('Poverty', '相对低收入面');
DICT.set('Histogram of county poverty rates', '区县相对低收入面分布');
DICT.set('Explore the data', '探索数据');
DICT.set('Level', '层级');
DICT.set('Chart', '图表');
DICT.set('None', '无');
DICT.set('Filter', '筛选');
DICT.set('others', '其他');
DICT.set('Active duty', '现役');
DICT.set('Reserve', '预备役');
DICT.set('National Guard', '国民警卫队');
DICT.set('Defense spending', '国防开支');
DICT.set('Veterans', '退伍军人');
DICT.set('Troops at home', '驻地兵力');
DICT.set('$ per resident', '人均国防开支');
DICT.set('Installations', '驻地');
DICT.set('Components', '军种');
DICT.set('Major', '主要');
DICT.set('Major & bases', '主要基地');
DICT.set('Every site', '全部站点');
DICT.set('Installation', '驻地');
DICT.set('Service', '军种');
DICT.set('Tier', '等级');

const ATTRS = ["placeholder", "title", "aria-label", "aria-description"];
const SKIP = new Set(["SCRIPT", "STYLE", "NOSCRIPT", "TEXTAREA", "CODE", "PRE", "CANVAS"]);
const CJK = /[\u3400-\u9fff]/;

function translate(value) {
  if (!value) return value;
  const lead = value.match(/^\s*/)[0], tail = value.match(/\s*$/)[0];
  const core = value.trim();
  if (!core) return value;
  if (DICT.has(core)) return lead + DICT.get(core) + tail;
  let out = core;
  // Mixed strings: names and numbers keep their content; common English fragments are translated.
  out = out.replace(/\bUS\b/g, "全国").replace(/\bU\.S\.\b/g, "全国");
  out = out.replace(/\bpeople\b/g, "人").replace(/\bemployed\b/g, "就业");
  out = out.replace(/\bworkers\b/g, "劳动者").replace(/\bresidents\b/g, "居民").replace(/\badults\b/g, "成年人");
  out = out.replace(/\bhexes\b/g, "格").replace(/\bhex\b/g, "格");
  out = out.replace(/Population: /g, "人口：").replace(/Unemployment rate: /g, "失业率：").replace(/\. Open the report/g, "。打开报告");
  out = out.replace(/Map layers \((\d+) of (\d+) on\)/g, "地图图层（$1/$2 开启）");
  out = out.replace(/City View: /g, "城市视图：");
  out = out.replace(/Show all (\d+)/g, "显示全部 $1 项");
  out = out.replace(/Year (\d{4}), current dollars/g, "$1 年，现价人民币");
  out = out.replace(/(\d+) of (\d+) metros/g, "$1 / $2 城市");
  out = out.replace(/\bmetros\b/g, "城市");
  out = out.replace(/^Source: /, "来源：");
  out = out.replace(/\bsince (\d{4})\b/g, "较 $1 年");
  out = out.replace(/\bper person\b/g, "人均");
  out = out.replace(/\bof residents\b/g, "的居民");
  out = out.replace(/\bEach figure ≈/g, "每个图标 ≈");
  out = out.replace(/\bin all\b/g, "总计");
  out = out.replace(/\bmedian age\b/gi, "年龄中位数");
  if (out !== core) return lead + out + tail;
  return value;
}

function walk(root) {
  if (!root) return;
  if (root.nodeType === Node.TEXT_NODE) {
    const p = root.parentElement;
    if (!p || SKIP.has(p.tagName) || p.closest("#map")) return;
    const next = translate(root.nodeValue);
    if (next !== root.nodeValue) root.nodeValue = next;
    return;
  }
  if (root.nodeType !== Node.ELEMENT_NODE) return;
  if (SKIP.has(root.tagName)) return;
  for (const a of ATTRS) {
    if (root.hasAttribute(a)) {
      const v = root.getAttribute(a);
      const next = translate(v);
      if (next !== v) root.setAttribute(a, next);
    }
  }
  for (const child of root.childNodes) walk(child);
}

export function localize(root = document.body) {
  walk(root);
}

let scheduled = 0;
function schedule() {
  if (scheduled) return;
  scheduled = requestAnimationFrame(() => { scheduled = 0; localize(document.body); });
}

const observer = new MutationObserver((records) => {
  for (const r of records) {
    for (const n of r.addedNodes) if (n.nodeType === Node.ELEMENT_NODE || n.nodeType === Node.TEXT_NODE) walk(n);
    if (r.type === "characterData") walk(r.target);
  }
});

export function installI18n() {
  localize(document.body);
  observer.observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ATTRS });
  schedule();
}


DICT.set('LOWER 48', '全国');
DICT.set('of the land', '土地占比');
DICT.set('crops + pasture', '耕地 + 牧草');
DICT.set('developed land', '建设用地');
DICT.set('Grassland', '草地');
DICT.set('Scrub & desert', '荒漠灌丛');
DICT.set('Cropland', '耕地');
DICT.set('Pasture & hay', '牧草');
DICT.set('Wetland', '湿地');
DICT.set('Forest lens', '森林镜头');
DICT.set("Each state's land cover type", '各省土地构成');
DICT.set('Table', '表格');
DICT.set('Grid', '网格');
DICT.set('above size thresholds', '规模以上');
DICT.set('oil &gas gas', '油气田');
DICT.set('MAPPED SITES ABOVE THRESHOLDS', '地图上的规模以上站点');
DICT.set('Growth 2020–2023', '2020–2023 人口增长');
DICT.set('Census estimates', '人口普查估计');
DICT.set('Growth by metro', '城市增长');
DICT.set('population change', '人口变化');
DICT.set('SHRINKING', '收缩城市');
DICT.set('Density', '密度');
DICT.set('Age', '年龄');
DICT.set('Foreign born', '境外出生');
DICT.set('counties', '区县');
DICT.set('States', '省份');
DICT.set('State', '省份');
DICT.set('persons', '人');
DICT.set('people', '人');
DICT.set('Share of the land in each cover type', '各地类的土地占比');
DICT.set('Hover a type to light up the hex', '悬停类型可高亮对应格子');
DICT.set('click to keep them lit', '点击可保持高亮');
DICT.set("The states' make-up", '各省土地构成');
DICT.set("Each state's land cover type. Sort by any cover; hover a state to outline it, click to open it.", '各省土地覆盖构成；可按任一类排序，悬停高亮，点击打开。');
DICT.set('All figures are public data', '所有数字均来自公开数据');

DICT.set('Hover or drag the scale to show only that range', '悬停或拖动色带，只显示该区间');
DICT.set('Click a swatch to show only it', '点击色块只看该类');
DICT.set('No data', '无数据');
DICT.set('Higher is better', '越高越好');
DICT.set('Higher is worse', '越低越好');
DICT.set('people / km²', '人/平方公里');
DICT.set('Click to open the city', '点击打开城市');
DICT.set('Click to open', '点击打开');
DICT.set('Native born', '本地出生');
DICT.set('NATIONAL REPORT', '全国报告');
DICT.set('LEADERBOARDS', '排行榜');
DICT.set('Source', '来源');
DICT.set('Show all', '显示全部');
DICT.set('Year 2024, current dollars', '2024 年，现价人民币');
DICT.set('Choose a lens', '选择镜头');
DICT.set('Base map', '底图');
DICT.set('Show the full legend', '显示完整图例');
DICT.set('Details', '详情');
DICT.set('Turn the lens off (back to terrain)', '关闭镜头（回到地形）');
DICT.set('Back to terrain', '返回地形');
DICT.set('Click a category to show only it', '点击类别只显示该类');

DICT.set('Turn the lens off (back to terrain)', '关闭镜头（回到地形）');
DICT.set('Highlight a range of values', '高亮数值区间');
DICT.set('Close lens picker', '关闭镜头选择');
DICT.set('Color by', '颜色按');
DICT.set('Map layers (4 of 4 on)', '地图图层（4/4 开启）');
DICT.set('GDP / person', '人均 GDP');
DICT.set('GDP / PERSON', '人均 GDP');
DICT.set('Generations', '代际');
DICT.set('Growth 2020–2023', '2020–2023 人口增长');

DICT.set('National report', '全国报告');
DICT.set('Leaderboards', '排行榜');
DICT.set('Show fewer', '收起');
DICT.set('Source:', '来源：');
DICT.set('Year', '年份');

DICT.set('Commute', '通勤');
DICT.set('COMMUTE', '通勤');
DICT.set('Education', '教育');
DICT.set('EDUCATION', '教育');
DICT.set('Origins', '出生地');
DICT.set('ORIGINS', '出生地');
DICT.set('Generations', '代际');
DICT.set('GENERATIONS', '代际');
DICT.set('Workforce', '劳动力');
DICT.set('WORKFORCE', '劳动力');
DICT.set('Citizens', '市民');
DICT.set('CITIZENS', '市民');

DICT.set('Columns', '列');
DICT.set('Add', '添加');
DICT.set('1M+', '100 万+');
DICT.set('250K+', '25 万+');
DICT.set('Tip: drag across the chart below to select a group.', '提示：在图表上拖框可选择一组地区。');
DICT.set('Choose what to compare, filter it, sort the table, and plot any two columns. Hover a row or a point to see it on the map; drag across the chart to select a group.', '选择比较对象、筛选、排序，并把任意两列画成散点图。悬停行或点会在地图上定位；在图上拖框可选择一组。');
DICT.set('Search cities & states', '搜索城市与省份');
DICT.set('Search cities and states', '搜索城市与省份');

installI18n();
