export const TOPICS = ["数据要素流通", "数据交易", "数据工厂", "数据质量评估", "高质量数据集", "可信数据空间"];
export const KINDS = ["法律法规", "政策文件", "研究报告", "标准", "技术文件", "行业动态", "政策解读"];
export type Document = {
  id: string; title: string; url: string; source: string; region: string;
  kind: string; status: string; date: string | null; issued?: string;
  number?: string; topics: string[]; summary: string; question: string;
  verified: boolean; collectedAt: string; dateLabel?: string;
};
const initial = "2026-10-18T08:30:00.000Z";
const make = (d: Omit<Document, "collectedAt" | "verified">): Document => ({...d, verified: true, collectedAt: initial});
export const SEEDS: Document[] = [
 make({id:"data-quality-model",title:"系统与软件工程 系统与软件质量要求和评价（SQuaRE） 第12部分：数据质量模型",url:"https://openstd.samr.gov.cn/bzgk/std/std_list?p.p1=0&p.p2=GB%2FT+25000.12-2017&p.p90=circulation_date&p.p91=desc",source:"国家标准全文公开系统",region:"全国",kind:"标准",status:"推荐性国家标准 · 引用前复核状态",date:"2017-11-01",number:"GB/T 25000.12-2017",topics:["数据质量评估"],summary:"关于数据质量模型的基础标准，可用于整理质量特性、搭建评估维度。正式引用前请在官方平台核对版本与现行状态。",question:"对照数据质量模型，哪些维度适合你的数据类型，哪些还需要针对任务补充？"}),
 make({id:"standards-2026",title:"关于发布2026年第二批数据领域国家标准需求的通知",url:"https://www.nda.gov.cn/sjj/zwgk/tzgg/1015/20261015155821338735862_pc.html",source:"全国数据标准化技术委员会秘书处（国家数据局刊载）",region:"全国",kind:"行业动态",status:"标准研制需求",date:"2026-10-15",issued:"2026-10-11",topics:["数据质量评估","高质量数据集","可信数据空间"],summary:"发布新一批数据领域国家标准需求清单，属于标准研制的前期需求征集，不是已发布实施的国家标准。",question:"对照附件的标准需求清单，寻找与你的研究方向相交的技术问题。"}),
 make({id:"industry-report",title:"《中国数据产业发展报告（2026）》在数博会开幕式发布",url:"https://www.nda.gov.cn/sjj/swdt/xwfb/0828/20260828233336307959824_pc.html",source:"国家数据局",region:"全国",kind:"行业动态",status:"报告发布消息",date:"2026-08-28",topics:["数据要素流通","数据交易","数据工厂"],summary:"介绍国家数据发展研究院在数博会发布的产业报告与趋势。此链接是发布消息，未将其标成报告全文。",question:"记录产业变化与新业态；引用具体统计口径前，查找报告全文。"}),
 make({id:"property-guide",title:"数据产权登记工作指引（试行）",url:"https://www.nda.gov.cn/sjj/zwgk/zcfb/0704/20260703230745065425855_pc.html",source:"国家数据局综合司",region:"全国",kind:"政策文件",status:"试行文件",date:"2026-07-04",issued:"2026-07-01",number:"国数综政策〔2026〕35号",topics:["数据要素流通","数据交易"],summary:"以统一的数据产权登记制度支撑数据安全合规流通，通知附有指引原文。",question:"数据登记与数据交易的关系是什么？登记能证明什么、不能证明什么？"}),
 make({id:"dataset-action",title:"关于推进行业高质量数据集建设行动的实施方案",url:"https://www.nda.gov.cn/sjj/zwgk/zcfb/0608/20260608172117399715004_pc.html",source:"国家数据局",region:"全国",kind:"政策文件",status:"正式发布",date:"2026-06-08",issued:"2026-06-03",number:"国数科基〔2026〕25号",topics:["高质量数据集","数据质量评估","数据工厂","可信数据空间"],summary:"部署行业数据集供给、标注、质量测评和应用等工作，提出建设数据赋能工场，连接数据加工、模型训练与应用。",question:"从采集、清洗、标注到评测，哪些环节可以成为你可验证的研究问题？"}),
 make({id:"digital-report",title:"数字中国发展报告（2025年）",url:"https://www.nda.gov.cn/sjj/swdt/xwfb/0608/ff808081-9e81e648-019e-a78ceae4-00c3.pdf",source:"国家数据局",region:"全国",kind:"研究报告",status:"报告全文 · PDF",date:"2026-06-08",issued:"2026年5月（报告署期）",dateLabel:"官方发布消息日期",topics:["数据要素流通","高质量数据集","可信数据空间"],summary:"梳理数字中国建设进展，可用于建立数据资源、基础设施及产业发展的宏观背景。",question:"摘出与你课题有关的背景证据，保留页码和统计年份。"}),
 make({id:"standard-pilot",title:"关于征集数据基础设施、高质量数据集等6个方向标准及技术文件验证试点单位的通知",url:"https://www.nda.gov.cn/sjj/ywpd/szkjyjcss/0402/20260402185936591334673_pc.html",source:"全国数据标准化技术委员会（国家数据局刊载）",region:"全国",kind:"行业动态",status:"历史试点通知",date:"2026-04-02",topics:["高质量数据集","数据质量评估","可信数据空间"],summary:"围绕数据基础设施、高质量数据集等方向开展标准验证。报名时间已过去，作为研究背景资料留存。",question:"标准验证通常需要怎样的实验场景和评价证据？"}),
 make({id:"dataset-quality-plan",title:"高质量数据集 质量评测规范",url:"https://std.samr.gov.cn/gb/search/gbDetailed?id=357E07163D46596BE06397BE0A0AD5D8",source:"全国标准信息公共服务平台",region:"全国",kind:"标准",status:"国家标准项目 · 非已实施标准",date:null,number:"20256913-T-907",topics:["高质量数据集","数据质量评估"],summary:"平台收录的推荐性国家标准制定项目，拟规范质量指标与评测细则。项目编号不能作为已发布的GB/T标准号引用。",question:"梳理质量维度与测评方法，并跟踪项目的后续发布状态。"}),
 make({id:"guizhou-law-2025",title:"贵州省大数据发展应用促进条例（2025年修订）",url:"https://www.gzrd.gov.cn/cwhgb_0/material/20256.pdf",source:"贵州省人大常委会公报",region:"贵州",kind:"法律法规",status:"2026-01-01施行（公告）",date:"2025-12-03",number:"贵州省人大常委会公告2025第17号",topics:["数据要素流通","数据交易","高质量数据集"],summary:"修订后的地方性法规涵盖算力、数据资源、应用赋能及安全管理等内容；链接为省人大公报原文。",question:"贵州地方制度如何衔接国家数据基础制度？整理相关条款及适用范围。"}),
 make({id:"data-factory-guide",title:"人工智能高质量数据集建设指南",url:"https://www.caict.ac.cn/english/research/whitepapers/202509/P020250924572568826648.pdf",source:"中国信息通信研究院",region:"全国",kind:"研究报告",status:"研究指南 · PDF",date:null,dateLabel:"发布日期（附件路径为2025年9月，具体日待核对）",topics:["数据工厂","高质量数据集","数据质量评估"],summary:"讨论人工智能数据集的工程建设与生产体系，包含数据工厂、自动化清洗和标注质检等实践思路。",question:"将数据工厂拆成输入、处理、质量控制与输出四部分，绘制你的研究流程。"}),
 make({id:"trusted-architecture",title:"可信数据空间 技术架构",url:"https://www.nda.gov.cn/sjj/ywpd/szkjyjcss/0430/20250430181352183912672_pc.html",source:"全国数据标准化技术委员会",region:"全国",kind:"技术文件",status:"技术文件 · 非国家标准",date:"2025-04-30",topics:["可信数据空间","数据要素流通"],summary:"描述可信数据空间的架构、基础功能和业务流程。它是技术文件，应与国家标准、地方标准分别引用。",question:"技术架构中的可信管控、资源交互与价值共创，分别对应哪些技术机制？"}),
 make({id:"trusted-action",title:"可信数据空间发展行动计划（2024—2028年）",url:"https://www.nda.gov.cn/sjj/zwgk/zcfb/1122/20241122164142182915964_mobile.html",source:"国家数据局",region:"全国",kind:"政策文件",status:"正式发布",date:"2024-11-23",issued:"2024-11-21",number:"国数资源〔2024〕119号",topics:["可信数据空间","数据要素流通"],summary:"从能力建设、培育推广与基础支撑等方面部署可信数据空间发展，是了解该方向政策背景的基础材料。",question:"从行动目标反推仍需解决的互操作、可信和治理问题。"}),
 make({id:"guizhou-trade",title:"贵州省数据流通交易促进条例",url:"https://www.gzrd.gov.cn/cwhgb_0/material/20244.pdf",source:"贵州省人大常委会公报",region:"贵州",kind:"法律法规",status:"2024-08-28施行（公告）",date:"2024-07-31",number:"贵州省人大常委会公告2024第8号",topics:["数据交易","数据要素流通"],summary:"围绕交易场所、授权使用、权益保护和安全保障建立贵州地方制度，是研究本地数据交易的重要基础文本。",question:"将交易主体、授权边界、权益保护与安全责任整理成条款对照表。"}),
 make({id:"data-twenty",title:"中共中央 国务院关于构建数据基础制度更好发挥数据要素作用的意见",url:"https://app.www.gov.cn/govdata/gov/202212/19/495422/article.html",source:"中国政府网",region:"全国",kind:"政策文件",status:"正式发布",date:"2022-12-19",issued:"2022-12-02",topics:["数据要素流通","数据交易"],summary:"通常称为“数据二十条”，从产权、流通交易、收益分配与安全治理建立研究数据要素的基本框架。",question:"用这四个维度为后续政策建立分类索引，观察国家与贵州制度的衔接。"}),
];

export type Source = {id: string; name: string; url: string; region: string; purpose: string};
export const SOURCES: Source[] = [
 {id:"nda",name:"国家数据局",url:"https://www.nda.gov.cn/sjj/index_pc.html",region:"全国",purpose:"政策发布、数据产业动态与标准化通知"},
 {id:"nda-policy",name:"国家数据局 · 政策发布",url:"https://www.nda.gov.cn/sjj/zwgk/zcfb/list/index_pc_1.html",region:"全国",purpose:"正式政策与配套解读，分别入库"},
 {id:"guizhou",name:"贵州省大数据发展管理局",url:"https://dsj.guizhou.gov.cn/",region:"贵州",purpose:"省内数据产业政策、试点与工作动态"},
 {id:"gzrd",name:"贵州人大",url:"https://www.gzrd.gov.cn/",region:"贵州",purpose:"地方性法规及修订动态；公报PDF人工核对"},
 {id:"caict",name:"中国信息通信研究院",url:"https://www.caict.ac.cn/kxyj/qwfb/bps/",region:"全国",purpose:"白皮书、研究报告与数据工程指南"},
];
export const REFERENCE_SOURCES = [
 {name:"全国标准信息公共服务平台",url:"https://std.samr.gov.cn/",purpose:"检索国家、行业、地方标准及项目状态；动态检索页面需人工核对"},
 {name:"全国数据标准化技术委员会",url:"https://www.tc609.org.cn/",purpose:"数据领域标准及技术文件的权威核对入口"},
 {name:"贵州财经大学信息学院",url:"https://xxxy.gufe.edu.cn/",purpose:"校内科研、学术活动与培养信息"},
];
