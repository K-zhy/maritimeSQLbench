schema_dict = {
    "maritime.vessel_reference": """-- maritime.vessel_reference 船舶基础信息主数据表：记录船舶的关键静态特征和属性，为船队管理、航运分析和海事监管提供基础数据支持。
    CREATE TABLE maritime.vessel_reference (
        "rid" int8 NOT NULL DEFAULT nextval('"maritime".vessel_reference_rid_seq'::regclass), -- 记录的唯一标识符 通常不使用该字段
        "mmsi" int4 NOT NULL,           -- 九位 海事移动服务识别码，船舶的唯一标识 主要使用字段
        "vessel_type" varchar,          -- 船舶类型（一级分类）[可选值: '10000', '20000', '30000', '40000', '50000', '60000']
        "vessel_sub_type" varchar,      -- 船舶子类型（二级分类）[可选值: '10200', '10400', '10600', '10800', '10900', '20300', '20500', '20600', '30100', '30300', '30600', '30700', '30800', '30820', '30830', '30840', '30850', '30900', '31000', '40400', '50100', '50200', '50300', '50400', '60300', '60400', '60500', '60700', '60820', '60830', '60900', '60910', '60920', '60930', '60950', '60970', '70000', '70200', '70300', '70500', '90000']
        "vessel_sub2_type" varchar,     -- 船舶细分类型（三级分类）[可选值: '20501', '20502', '20503', '20504', '20506', '20508', '30101', '30301', '30601', '30701', '30102', '30302', '30602', '30702', '30103', '30303', '30603', '30703', '30104', '30304', '30604', '30704', '30105', '30305', '30605', '30106', '30306', '30606', '30801', '30901', '30802', '30902', '30821', '30831', '30822', '30832', '30823', '30833', '30824', '30834', '30825', '30835', '30826', '30836', '31001', '31002', '31003', '31004', '31005', '20302', '20304', '20306', '20308', '20310', '40401', '40402', '40403', '40404', '40405', '40406', '40407', '90010', '90020', '90030']
        "imo" varchar,                  -- 七位 国际海事组织编号，船舶的永久标识
        "callsign" varchar,             -- 船舶呼号，用于无线电通信
        "name_en" varchar,              -- 船舶英文名称
        "name_cn" varchar,              -- 船舶中文名称
        "name_pinyin" varchar,          -- 船舶名称拼音全拼
        "name_py" varchar,              -- 船舶名称拼音缩写
        "flag_ctry" varchar,            -- 船旗国，船舶注册的国家英文缩写
        "registry_port" varchar,        -- 船籍港，船舶注册的港口
        "class_society" varchar,        -- 船级社，负责船舶检验和认证的机构英文缩写
        "build_year" varchar,           -- 建造年份
        "build_year_month" varchar,     -- 建造年月，格式：YYYYMM
        "retire_year_month" int4,       -- 退役年月，格式：YYYYMM
        "dwt" int4,                     -- 载重吨，船舶可以安全装载的最大重量（吨）
        "grt" int4,                     -- 总吨位，船舶所有密闭空间的体积
        "net" int4,                     -- 净吨位，船舶可用于装载货物的空间体积
        "teu" int4,                     -- 标准箱位数，集装箱船可装载的20尺标准集装箱数量
        "liquid" int4,                  -- 液货舱容量（立方米）
        "gas" int4,                     -- 气体舱容量（立方米）
        "length" numeric(5,1),          -- 船长（米）
        "width" numeric(5,1),           -- 船宽（米）
        "height" numeric(5,1),          -- 船高（米）
        "draught" numeric(5,3),         -- 设计吃水深度（米）
        "speed" numeric(5,1),           -- 设计航速（节）
        "operator_body" varchar,        -- 主体: 船舶经营主体（英文）
        "manage_body" varchar,          -- 主体: 船舶管理公司（英文）
        "owner_body" varchar,           -- 主体: 船舶所有者（英文）
        "fleet_body" varchar,           -- 所属船队（英文）
        "calibre" int2,                 -- 船舶归属：1-集团自有，2-集团租赁，3-集团外[可选值: 1, 2, 3]
        "from_lr" int2,                 -- 数据是否来自劳氏船级社：1-是，0-否[可选值: 0, 1]
        "pre_mmsi" int4,                -- 船舶前一次使用的MMSI号
        "operator_body_cn" varchar,     -- 主体: 船舶经营主体（中文）
        "manage_body_cn" varchar,       -- 主体: 船舶管理公司（中文）
        "owner_body_cn" varchar,        -- 主体: 船舶所有者（中文）
        PRIMARY KEY ("rid", "mmsi"),
        UNIQUE ("mmsi")
    );
""",
    "maritime.vessel_state_history":"""
    -- maritime.vessel_state_history 船舶动态历史表：记录船舶所有状态变化的历史信息。每当船舶状态改变（如航行转为锚泊、锚泊转为靠泊等）时，会生成新的动态记录。
    -- 该表为航运分析、船舶跟踪和航线优化提供了全面的数据支持。
    -- 注意: dynamic_type = 5 即产生靠泊/作业行为时，是不同航段的分隔点，即一个航段的最后一个状态。这个时候会补充整个航段的缺失信息。
    -- 特别注意 → 请理解并每个字段后面的字段有效说明 :  的原因是当 is_new=1 的时候，字段记录还不会被更新。|   指的是当一个航段最后一个状态才会记录的信息。
    -- 特别注意 → 询问‘动态’的时候请使用此表
    CREATE TABLE maritime.vessel_state_history(
        "uuid" varchar,                 -- 记录的唯一标识符，用于区分不同的动态记录。
        "mmsi" integer NOT NULL,        -- MMSI 船舶的海事移动服务识别码，是识别特定船舶的主要字段 用于AIS系统中识别船舶。
        "dynamic_type" varchar,         -- 船舶动态类型：0-航行，1-锚泊，5-靠泊(作业)，6-搁浅。反映船舶当前的活动状态，对分析船舶行为模式至关重要。[可选值: '0', '1', '5', '6']
        "is_new" smallint NOT NULL DEFAULT 0, -- 标识是否为最新动态：1-是，0-否。用于快速定位船舶的最新状态。[可选值: 0, 1]
        "start_postime" timestamp with time zone NOT NULL, -- 不同动态开始的UTC时间，记录每个动态船舶状态变化的精确起始时间点。如当 dynamic_type==5，start_postime 表示船舶靠泊时间。
        "start_postime_local" timestamp with time zone, -- 动态开始的当地时间，便于分析不同时区的操作。
        "end_postime" timestamp with time zone, --  动态结束的UTC时间，记录状态变化的终止点 。
        "end_postime_local" timestamp with time zone, --  动态结束的当地时间，配合开始时间计算持续时间 。
        "start_lon" numeric(11,6),      -- 动态开始时的经度，精确到小数点后6位。
        "start_lat" numeric(11,6),      -- 动态开始时的纬度，精确到小数点后6位。
        "end_lon" numeric(11,6),        --  动态结束时的经度，用于计算移动距离和方向。
        "end_lat" numeric(11,6),        --  动态结束时的纬度，用于计算移动距离和方向。
        "start_eta" timestamp with time zone, -- 动态开始时预计到达目的地时间(ETA)，反映初始航行计划。
        "end_eta" timestamp with time zone, --  动态结束时预计到达目的地时间(ETA)，用于跟踪ETA的变化。
        "seg_duration" numeric(11,2),   -- 该动态持续的时长（小时），用于分析不同状态的持续时间。
        "start_draught" numeric(11,2),  -- 动态开始时船舶吃水深度（米），反映载重情况。
        "end_draught" numeric(11,2),    --  动态结束时船舶吃水深度（米），用于分析载重变化。
        "draught_diff" numeric(11,2),   --  吃水深度变化（米），直接反映装卸货量。
        "is_port_moor" smallint,        -- 锚泊类型：1-港口锚泊，0-中途锚泊。区分本次锚泊是在港口还是在航途中锚泊。[可选值: 0, 1]
        "moor_port_code" varchar,       -- 锚泊港口代码，用于识别船舶锚泊的具体港口。
        "is_direct" smallint,           -- 本次靠泊是否是直接靠泊（未经锚泊）：1-是，0-否。[可选值: 0, 1]
        "berth_duration" numeric(11,2), -- 靠泊时长（小时），即靠泊后到离港前的作业时间。
        "arrival_time" timestamp with time zone, -- 船舶到港时间，记录实际抵达港口的时刻。
        "arrival_time_local" timestamp with time zone, -- 船舶到港当地时间，便于分析不同时区的港口操作。
        "is_canal" smallint,            -- 是否为运河：1-是，0-否。用于识别船舶是否正在通过重要水道。[可选值: 0, 1]
        "canal_moor_position" varchar,  -- 运河锚地位置，指示船舶在运河上游或下游的具体锚泊位置。
        "leg_start_postime" timestamp with time zone, -- 航段开始时间（UTC），标记一个完整航程的起点。
        "leg_start_postime_local" timestamp with time zone, -- 航段开始当地时间，便于分析不同时区的航程。
        "leg_end_postime" timestamp with time zone, -- 航段结束时间（UTC），标记一个完整航程的终点。
        "leg_end_postime_local" timestamp with time zone, -- 航段结束当地时间，用于计算航程持续时间。
        "leg_start_year_month" varchar, -- 航段开始的年月（YYYYMM格式），便于按月份统计和分析航运数据。
        "leg_end_year_month" varchar,   -- 航段结束的年月（YYYYMM格式），便于跨月航程的分析。
        "leg_start_port_code" varchar,  -- 航段起始港口代码，用于识别航程的出发点。
        "leg_end_port_code" varchar,    -- 航段终止港口代码，用于识别航程的目的地。
        "leg_cross_nodes" varchar,      -- 航段穿越的重要节点字符串，记录船舶经过的关键地理位置或航运节点。
        "leg_duration_total" numeric(11,2), -- 航段总时长（小时），反映完整航程的持续时间。
        "is_ais_abnormal" smallint NOT NULL DEFAULT 0, -- 航段期间AIS信号是否异常（丢失超过10天）：1-异常，0-正常。用于评估数据质量和船舶安全。[可选值: 0, 1]
        "max_lost_duration" integer,    --   航段期间AIS信号最大丢失时长（小时）。
        "is_repaired" smallint,         -- 航段期间是否有维修记录：1-有，0-无。反映船舶维护情况。[可选值: 0, 1]
        "repair_shipyard" varchar,      -- 维修船厂名称，用于分析维修地点和频率。
        "is_full_load" smallint,        -- 航段期间是否满载：1-满载，0-非满载。指示船舶载重状态，反映运力利用情况。[可选值: 0, 1]
        "load_type" smallint,           --   航段期间装卸货类型：1-装货，0-卸货。标识货物流向。[可选值: 0, 1]
        "load_port_code" varchar,       --   当前卸货港的上一个装货港代码，用于分析货物来源。
        "moor_times_port" integer,      --   航段期间港口锚泊次数，指示在港口区域的停留情况，分析港口拥堵情况。
        "moor_times_halfway" integer,   --   航段期间中途锚泊次数，反映航行中的非计划停靠。
        "moor_times_total" integer,     --   航段期间总锚泊次数 moor_times_port + moor_times_halfway 。
        "moor_duration_port" numeric(11,2), --   航段期间港口锚泊总时长（小时），评估港口效率。
        "moor_duration_halfway" numeric(11,2), --   航段期间中途锚泊总时长（小时），分析航行中断原因。
        "moor_duration_total" numeric(11,2), --   航段期间锚泊总时长（小时）即 moor_duration_port + moor_duration_halfway。
        "sail_duration" numeric(11,2),  --  当前动态期间航行总时长（小时），反映当前状态航行时间。
        "sail_distance" numeric(11,2),  --  当前动态期间航行期间航行总里程（海里），反映当前状态航行距离。 
        "average_speed" numeric(11,2),  --  航段期间平均航速（节），反映航行效率。
        "update_time" timestamp with time zone, -- 记录更新时间，用于跟踪数据变更。
        "berth_uuid" varchar,           --   泊位唯一标识符，关联具体泊位信息。
        "total_lost_duration" smallint, --   AIS信号总丢失时长（小时），评估数据质量。
        "ais_lost_rate" numeric(5,2),   --   AIS信号丢失率，计算数据完整性百分比，反映数据质量和覆盖范围。
        "ais_abnormal_times" smallint,  --   AIS异常次数，反映信号不稳定频率。
        "schedule_time" timestamp with time zone, -- 计划时间，用于比较实际与计划的偏差。
        "load_type_source" varchar,     --   装载类型来源，标识数据可靠性。
        "leg_uuid" varchar,             -- 航段的唯一标识符，用于关联同一航段的所有记录。
        "leg_start_berth_uuid" varchar, -- 航段起始靠泊记录的唯一标识符，链接到详细的靠泊信息。
        "leg_sail_distance" numeric(11,2), -- 当前航段航行总里程（海里），反映当前当前航段航行距离(即 dynamic_type = 0 )的累计值。
        "leg_sail_duration" numeric(11,2), -- 当前航段航行总时长（小时），反映当前当前航段航行时间(即 dynamic_type = 0 )的累计值。
        "pre_start_draught" numeric(4,1) -- 上一靠泊港的进港吃水（米），用于分析装卸货影响。
    ) PARTITION BY RANGE ("start_postime");

    """,
    "maritime.vessel_event_log":"""
    -- maritime.vessel_event_log 船舶事件表 - 异常风险事件表
    -- 业务用途：记录并追踪船舶航行过程中的异常和风险事件，为船舶安全预警和风险评估提供数据支持
    -- 1. 船舶会遇(EVENT_ENCOUNTER)：记录开阔水域的船舶会遇情况，用于分析船舶会遇风险
    -- 2. 新闻事件(EVENT_MANUAL)：人工记录的重要船舶事故信息，用于事故分析和统计
    -- 3. 恶劣天气(EVENT_RISK)：包括台风、大风浪、大雾等气象风险，用于气象风险预警
    CREATE TABLE maritime.vessel_event_log (
        "uuid" varchar NOT NULL DEFAULT replace((uuid_generate_v4())::text, '-'::text, ''::text), -- 事件的唯一标识符
        "mmsi" int4,                    -- 船舶的海事移动服务识别码（Maritime Mobile Service Identity）
        "composite_key" varchar,        -- 事件联合标识，例如加油作业时为加油船的MMSI
        "event_name_code" varchar,      -- 事件名称编码，[可选值: 'EVENT_ACHOR', 'EVENT_ENCOUNTER', 'EVENT_MANUAL', 'EVENT_STS', 'EVENT_RISK', 'EVENT_SPEED', 'EVENT_CROSS']
        "event_type_code" varchar,      -- 事件类型编码，[可选值: 'DEPART', 'BERTH', 'MOOR', 'SAIL', 'ENCOUNTER', 'ACCIDENT', 'STS_TUG', 'STS_OIL', 'STS_LOAD', 'TYPHOON_ENCIRCLE', 'TYPHOON_AFFECT', 'WAVE', 'WIND', 'FOG', 'SPEED_LOW', 'STRANDED', 'DRAGGING_ANCHOR', 'DRIFTING_SAIL', 'ICE', 'YSW', 'SWZ', 'NBO-MONITOR', 'TTZ', 'CN_BREED_REGION', 'PRZ']
        "event_time" timestamptz(6),    -- 事件发生的UTC时间
        "event_local_time" timestamptz(6), -- 事件发生的当地时间
        "lon" numeric(11,6),            -- 事件发生的经度坐标
        "lat" numeric(11,6),            -- 事件发生的纬度坐标
        "sea_region_cn" varchar,        -- 事件发生的海域中文描述[可选值: '珠江', '弗洛勒斯海', '地中海东部水域', '菲律宾海', '楚科奇海', '南太平洋(西)', '巴伦支海', '黑海', '阿拉伯海', '中国东海', '哈德逊湾', '挪威海', '爪哇海', '北冰洋', '圣劳伦斯湾', '苏禄海', '苏伊士运河', '莫桑比克 海峡', '红海', '北海', '爱琴海', '北太平洋(东)', '加利福尼亚湾', '塞兰海', '北大西洋', '塔斯曼海', '亚得里亚海', ' 日本海', '拉克代夫海', '巴芬湾', '巴拿马运河', '苏格兰西海岸内部水域', '戴维斯海峡', '北美五大湖', '巴利阿里海', ' 阿尔伯兰海', '阿拉斯加东南部和不列颠哥伦比亚省沿海水域', '墨西哥湾', '东西伯利亚海', '比斯开湾', '南太平洋(东)', ' 拉普捷夫海', '班达海', '阿拉弗拉海', '波罗的海', '中国南海', '地中海西部水域', '加勒比海', '西北通道', '马六甲海峡', '白令海', '巴斯海峡', '阿曼湾', '巴厘海', '鄂霍次克海', '俾斯麦海', '波弗特海', '马鲁古海', '帝汶海', '西里伯斯海', '大澳大利亚湾', '北太平洋(西)', '阿拉斯加湾', '渤海', '孟加拉湾', '哈德逊海峡', '南大西洋', '拉布拉多海', '波尼 湾', '芬兰湾', '哈马黑拉海', '南极大洋', '所罗门海', '缅甸海', '黄海', '格陵兰海', '印度洋', '珊瑚海', '喀拉海', ' 芬迪湾', '长江', '白海', '爱奥尼亚海', '布里斯托尔海峡', '英吉利海峡', '直布罗陀海峡', '泰国湾', '加泰罗尼亚海', ' 卡特加特海峡', '爱尔兰海和圣乔治海峡', '新加坡海峡', '斯卡格拉克海峡', '亚丁湾', '拉普拉塔河', '马尔马拉海', '几内 亚湾', '托米尼湾', '苏伊士湾', '利古里亚海', '波的尼亚湾', '伊特鲁里亚海', '望加锡海峡', '亚喀巴湾', '林肯海', '里 加湾', '萨武海', '波斯湾', '亚述海']
        "sea_region_en" varchar,        -- 事件发生的海域英文描述[可选值: 'The Pearl River', 'Flores Sea', 'Mediterranean Sea - Eastern Basin', 'Philippine Sea', 'Chukchi Sea', 'South Pacific Ocean(West)', 'Barentsz Sea', 'Black Sea', 'Arabian Sea', 'Eastern China Sea', 'Hudson Bay', 'Norwegian Sea', 'Java Sea', 'Arctic Ocean', 'Gulf of St. Lawrence', 'Sulu Sea', 'Suez Canal', 'Mozambique Channel', 'Red Sea', 'North Sea', 'Aegean Sea', 'North Pacific Ocean(East)', 'Gulf of California', 'Ceram Sea', 'North Atlantic Ocean', 'Tasman Sea', 'Adriatic Sea', 'Japan Sea', 'Laccadive Sea', 'Baffin Bay', 'Panama Canal', 'Inner Seas off the West Coast of Scotland', 'Davis Strait', 'Great Lakes of North America', 'Balearic (Iberian Sea)', 'Alboran Sea', 'The Coastal Waters of Southeast Alaska and British Columbia', 'Gulf of Mexico', 'East Siberian Sea', 'Bay of Biscay', 'South Pacific Ocean(East)', 'Laptev Sea', 'Banda Sea', 'Arafura Sea', 'Baltic Sea', 'South China Sea', 'Mediterranean Sea - Western Basin', 'Caribbean Sea', 'The Northwestern Passages', 'Malacca Strait', 'Bering Sea', 'Bass Strait', 'Gulf of Oman', 'Bali Sea', 'Sea of Okhotsk', 'Bismarck Sea', 'Beaufort Sea', 'Molukka Sea', 'Timor Sea', 'Celebes Sea', 'Great Australian Bight', 'North Pacific Ocean(West)', 'Gulf of Alaska', 'Bohai Sea', 'Bay of Bengal', 'Hudson Strait', 'South Atlantic Ocean', 'Labrador Sea', 'Gulf of Boni', 'Gulf of Finland', 'Halmahera Sea', 'Southern Ocean', 'Solomon Sea', 'Andaman or Burma Sea', 'Yellow Sea', 'Greenland Sea', 'Indian Ocean', 'Coral Sea', 'Kara Sea', 'Bay of Fundy', 'The Yangtse River', 'White Sea', 'Ionian Sea', 'Bristol Channel', 'English Channel', 'Strait of Gibraltar', 'Gulf of Thailand', 'Celtic Sea', 'Kattegat', "Irish Sea and St. George's Channel", 'Singapore Strait', 'Skagerrak', 'Gulf of Aden', 'Rio de La Plata', 'Sea of Marmara', 'Gulf of Guinea', 'Gulf of Tomini', 'Gulf of Suez', 'Ligurian Sea', 'Gulf of Bothnia', 'Tyrrhenian Sea', 'Makassar Strait', 'Gulf of Aqaba', 'Lincoln Sea', 'Gulf of Riga', 'Savu Sea', 'Persian Gulf', 'Sea of Azov']
        "event_location_cn" varchar,    -- 事件发生位置的中文描述
        "event_location_en" varchar,    -- 事件发生位置的英文描述
        "event_weather_cn" varchar,     -- 事件发生时的天气状况中文描述
        "event_weather_en" varchar,     -- 事件发生时的天气状况英文描述
        "event_desc_cn" varchar,        -- 事件的中文详细描述
        "event_desc_en" varchar,        -- 事件的英文详细描述
        "wind_val" numeric(11,2),       -- 事件发生时的风速（米/秒）
        "wind_direction" numeric(11,2), -- 事件发生时的风向（度数）
        "wind_cross_type" varchar,      -- 风向相对于船舶航行方向的类型：TAIL（顺风），SIDE_TAIL（侧顺风），HEAD（逆风），SIDE_HEAD（侧逆风），CROSS（正横风）[可选值: 'TAIL', 'SIDE_TAIL', 'HEAD', 'SIDE_HEAD', 'CROSS']
        "wave_val" numeric(11,2),       -- 事件发生时的浪高（米）
        "wave_direction" numeric(11,2), -- 事件发生时的浪向（度数）
        "wave_cross_type" varchar,      -- 浪向相对于船舶航行方向的类型：TAIL（顺浪），SIDE_TAIL（侧顺浪），HEAD（逆浪），SIDE_HEAD（侧逆浪），CROSS（正横浪）[可选值: 'TAIL', 'SIDE_TAIL', 'HEAD', 'SIDE_HEAD', 'CROSS']
        "stream_val" numeric(11,2),     -- 事件发生时的流速（米/秒）
        "stream_direction" numeric(11,2), -- 事件发生时的流向（度数）
        "stream_cross_type" varchar,    -- 流向相对于船舶航行方向的类型：TAIL（顺流），SIDE_TAIL（侧顺流），HEAD（逆流），SIDE_HEAD（侧逆流），CROSS（正横流）[可选值: 'TAIL', 'SIDE_TAIL', 'HEAD', 'SIDE_HEAD', 'CROSS']
        "temperature_val" numeric(11,2), -- 事件发生时的气温（摄氏度）
        "pressure_val" numeric(11,2),   -- 事件发生时的气压（帕斯卡）
        "sow" numeric(5,1),             -- 船舶对水速度（米/秒）
        "extend_info" jsonb,            -- 事件相关的扩展信息（JSON格式）
        "record_time" timestamptz(6) DEFAULT now(), -- 事件记录创建时间
        PRIMARY KEY ("uuid")
    ) PARTITION BY RANGE ("event_time");

 
""",
    "maritime.vessel_current_state":"""
    -- maritime.vessel_current_state 船舶实时状态表：记录每艘船舶(MMSI)的当前状态，存储了船舶的实时位置、航行状态、目的地、预计抵达时间等信息.
    CREATE TABLE maritime.vessel_current_state
    (
    -- 船舶基础识别信息
    "mmsi" integer NOT NULL, -- 船舶的MMSI号，用于唯一标识船舶
    "ais_imo" varchar, -- 船舶IMO编号
    "ais_callsign" varchar, -- 船舶呼号
    "retire_year_month" varchar, -- 退役年月(YYYYMM) | 如果该字段有值 则该条数据为无效数据

    -- 当前AIS状态信息
    "ais_status" smallint, -- 当前AIS航行状态码 
    "ais_postime" timestamp with time zone, -- AIS位置信息更新时间(UTC)
    "sog" numeric(11,2), -- 对地航速(Speed Over Ground)，单位：节
    "hdg" numeric(11,2), -- 船艏向(Heading)，单位：度
    "cog" numeric(11,2), -- 对地航向(Course Over Ground)，单位：度
    "draught" numeric(11,2), -- 设计吃水深度，单位：米
    "ais_draught" numeric(11,2), -- 当前吃水深度，单位：米
    "lon" numeric(11,6), -- 当前经度
    "lat" numeric(11,6), -- 当前纬度
    "ais_dest" varchar, -- AIS报告的目的地
    "ais_eta" timestamp with time zone, -- AIS报告的预计到达时间

    -- 动态类型信息
    "dynamic_type" varchar, -- 当前动态类型：'0'-航行，'1'-锚泊，'5'-靠泊，'6'-搁浅[可选值: '0', '1', '5', '6']
    -- 港口相关信息
    "start_port_code" varchar, -- 当前航段的起始港口代码
    "end_port_code" varchar, -- 当前航段的目标港口代码 (预计)
    "moor_port_code" varchar, -- 当前锚泊港口代码（如果处于锚泊状态）
    "is_port_moor" smallint, -- 当前是否在港口锚地：1-是，0-否[可选值: 0, 1]
    "is_canal" smallint, -- 当前是否在运河区域：1-是，0-否[可选值: 0, 1]
    -- 预计时间信息
    "eta" timestamp with time zone, -- 系统计算的预计到达时间(UTC)
    "eta_local" timestamp with time zone, -- 系统计算的预计到达时间(本地时间)
    "cta" timestamp with time zone, -- 修正后的预计到达时间(UTC) 使用该字段查询预计抵港时间
    "atd" timestamp with time zone, -- 实际离港时间(UTC)
    "ata" timestamp with time zone, -- 实际到港时间(UTC)
    "estimate_berth_time" timestamp with time zone, -- 预计靠泊时间
    "estimate_depart_time" timestamp with time zone, -- 预计离泊时间

    -- 航程计算相关
    "sail_duration" numeric(11,2), -- 航段已航行时长（小时）
    "sail_distance" numeric(11,2), -- 航段已航行距离（海里）
    "line_distance" numeric(11,2), -- 航段总里程（海里）
    "rest_hour" numeric(11,2), -- 预计剩余航行时间（小时）
    "rest_distance" numeric(11,2), -- 预计剩余距离（海里）
    "delay_duration" numeric(11,2), -- 延误时长（小时）
    "ct_offset" numeric(11,2), -- 时区偏移（小时）
    "avg_leg_duration" numeric(11,2), -- 历史平均航程时长（小时）
    "cta_duration_diff" numeric(11,2), -- CTA与平均航程时长的差值（小时）
    
    PRIMARY KEY ("mmsi"),
    UNIQUE ("mmsi")

    ) PARTITION BY RANGE ("start_postime");
    COMMENT ON TABLE maritime.vessel_current_state IS '
    船舶实时状态表功能说明：

    1. AIS基础信息跟踪
    - 实时更新船舶位置、航速、航向等AIS广播数据
    - 监控船舶动态状态（航行/锚泊/靠泊/搁浅）
    - 记录当前吃水深度反映载重情况

    2. 航段进度管理
    - 跟踪当前航段起始港与目标港信息
    - 统计已航行距离和时间
    - 计算剩余航程和预计时间

    3. 到港预测服务
    - 提供AIS广播ETA、系统计算ETA、修正后CTA
    - 支持UTC和本地时间显示
    - 提供靠离泊时间预测
    ';
   
    """,
    "maritime.index_observation":"""
    -- maritime.index_observation 航运指数表：记录和追踪各种航运市场指数的日常变化，用于分析航运市场趋势和波动
    CREATE TABLE maritime.index_observation (
        "rid" SERIAL NOT NULL,              -- 记录ID：自动递增的唯一标识符
        "index_code" varchar,               -- 航运指数编码：对应不同类型的航运指数 详情见 maritime.index_catalog
        "curr_value" numeric(11,2),         -- 当前指数值：反映最新的航运市场行情，可用于评估当前市场状况
        "pre_value" numeric(11,2),          -- 上一期指数值：用于与当前值比较，计算市场变化
        "increment" numeric(11,2),          -- 指数增量值：当前值与上一期值的差额，反映市场变化的绝对量
        "increment_percent" numeric(11,2),  -- 指数增量百分比：增量值占上一期值的百分比，反映市场变化的相对幅度
        "value_date" date,                  -- 指数日期：当前指数值的对应日期
        "is_new" smallint NOT NULL DEFAULT 0, -- 是否为最新记录：1表示是当前指数的最新记录，0表示历史记录[可选值: 0, 1]
        "create_time" timestamp with time zone, -- 记录创建时间：数据入库的时间戳，包含时区信息，用于追踪数据更新情况
        "uuid" varchar,                     -- 同步唯一键：用于数据集成和同步
        PRIMARY KEY ("rid")
    );

    -- maritime.index_observation 样例数据:
    /*
    Columns in maritime.index_observation and 3 examples in each column for the high cardinality columns:
        rid(SERIAL): 12545, 12546, 413011
        curr_value(numeric(11,2)): 1246.28, 1222.38, 1257.00
        pre_value(numeric(11,2)): 1239.03, 1213.81, 1260.00
        increment(numeric(11,2)): 7.25, 8.57, -3.00
        increment_percent(numeric(11,2)): 0.59, 0.71, -0.24
        value_date(date): 2021-08-13, 2021-08-13, 2024-10-16
        create_time(timestamp with time zone): 2021-08-20 19:57:07.828906+08, 2021-08-20 19:57:07.828906+08, 2024-10-17 08:05:52.604717+08
        uuid(varchar): ANONYMIZED_VALUE_13, , ANONYMIZED_VALUE_15, 
    */
    """,
    "maritime.index_catalog":"""
    -- maritime.index_catalog 航运指数代码表：存储和管理各种航运指数的元数据信息

    CREATE TABLE maritime.index_catalog (
        "rid" SERIAL NOT NULL,              -- 记录ID：自动递增的唯一标识符
        "parent_code" varchar,              -- 父级指数代码：用于表示指数的层级关系
        "index_code" varchar,               -- 航运指数编码
        "name_cn" varchar,                  -- 指数中文名称
        "name_en" varchar,                  -- 指数英文名称
        "data_source" varchar,              -- 指数数据来源[可选值: 'WIND', 'csi', 'drewry', 'eworldship', 'sse', 'wind']
        "source_detail" varchar,            -- 数据源详细信息：包括数据获取的 URL 或其他相关描述
        "update_term" varchar,              -- 指数更新周期：如 d1（每日）、d7（每周）、h3（每3小时）等
        "threshold_alert" integer,          -- 数据缺失告警阈值：超过该天数未更新数据时触发告警
        "last_update_time" date,            -- 最后更新日期：记录该条目最后一次维护的日期
        "is_void" smallint DEFAULT 0,       -- 是否作废：0 表示有效，1 表示作废，仅此字段为 0 的数据记录有效[可选值: 0, 1]
        PRIMARY KEY ("rid")
    );

    -- maritime.index_catalog 样例数据:
    /*
    Columns in maritime.index_catalog and 3 examples in each column for the high cardinality columns:
        rid(SERIAL): 2, 1, 196
        parent_code(varchar): CCBFI, , SCFIS
        index_code(varchar): CCBFI-BULK, CCBFI, SCFIS-WA
        name_cn(varchar): 沿海干散货指数, 中国沿海散货运价指数, SCFIS:美西航线(基本港)
        name_en(varchar): COASTAL BULK FREIGHT INDEX, CHINA COASTAL BULK FREIGHT INDEX, 
        source_detail(varchar): 
        update_term(varchar): d1, d7, h3
        threshold_alert(integer): 3, , 15
        last_update_time(date): 2022-02-25, 2022-02-25, 2020-12-24
    */

    """,
    "maritime.port_reference":"""
    -- maritime.port_reference 全球港口基础信息表：记录了全球各地港口的详细信息，包括地理位置、名称、类型等关键数据
    CREATE TABLE maritime.port_reference (
        "port_code" varchar NOT NULL,       -- 港口唯一代码，用于标识不同的港口
        "port_type" varchar,                -- 港口类型：B-基本港，T-普通码头，O-原油码头，F-浮仓[可选值: 'B', 'T', 'O', 'F']
        "ctry_code" varchar,                -- 港口所属国家的代码
        "port_area_code" varchar,           -- 港口区域代码，1表示海区，空表示非海区[可选值: '1', '']
        "name_en" varchar,                  -- 港口英文名称
        "name_cn" varchar,                  -- 港口中文名称
        "name_pinyin" varchar,              -- 港口中文名称的拼音全称
        "name_py" varchar,                  -- 港口中文名称的拼音缩写
        "lon" numeric(11,6),                -- 港口经度坐标
        "lat" numeric(11,6),                -- 港口纬度坐标
        "position" public.geography,        -- 港口的地理位置，使用PostgreSQL的geography数据类型存储
        "tz_offset" smallint,               -- 港口所在时区相对于UTC的偏移小时数
        "extra_lon_lat" varchar,            -- 港口其他重要位置的经纬度信息，多个位置用竖线"|"分隔
        "port_in_code" varchar,             -- 港口所属更大港口区域的代码（如果适用）
        "port_desc" varchar,                -- 港口的详细描述，包括地理位置、重要性等信息
        "alias_names" varchar,              -- 港口的别名或其他常用名称
        "unlocode" varchar(255),            -- 联合国贸易和运输位置代码（UN/LOCODE）
        "unloname" varchar(255),            -- 与UN/LOCODE相关的官方港口名称
        "unloctry" varchar(255),            -- 与UN/LOCODE相关的国家或地区名称
        PRIMARY KEY ("port_code")
    );

    -- maritime.port_reference 样例数据:
    /*
    Columns in maritime.port_reference and 3 examples in each column for the high cardinality columns:
        port_code(varchar): CNYSN, CNZOS, CNSHA, NLROT, SGSGP, CNQIN, DEHAM, CNTJN
        ctry_code(varchar): CN, MY, SX
        name_en(varchar): YANGSHAN, PORT WELD, PHILIPSBURG
        name_cn(varchar): 上海-洋山, 宁波-舟山, 上海, 鹿特丹, 新加坡, 青岛, 汉堡, 天津
        name_pinyin(varchar): SHANGHAI-YANGSHAN, WENDEGANG, FEILIPUSIBAO
        name_py(varchar): SH-YS, WDG, FLPSB
        lon(numeric(11,6)): 122.066667, 100.633333, -63.052254
        lat(numeric(11,6)): 30.633333, 4.833333, 18.021834
        position(public.geography): ANONYMIZED_VALUE_07, ANONYMIZED_VALUE_09, ANONYMIZED_VALUE_08
        tz_offset(smallint): 8, 8, -4
        extra_lon_lat(varchar): (55.969980,25.977072), , (11.264,-6.247)|(11.143,-6.347)|(11.037,-6.328) 
        port_in_code(varchar): AERAK, ,CNSHA
        port_desc(varchar): "位于阿联酋（全称：阿拉伯联合酋长国 THE UNITED ARAB EMIRATES）中部沿海的一个小岛上，BALABALA", , "阿治曼港位于位于阿拉伯海湾或波斯湾出入口通道附近，战略位置十分重要，而且紧靠沙迦和迪拜，交通运输网络完备, Balabala"
        alias_names(varchar): FREDERIKSHAAB, MINA ZAYED, 
        unlocode(varchar): CABAD, ESSNA, ITMDA
        unloname(varchar): Baddeck, La Salineta, La Maddalena (Sardinia)
        unloctry(varchar): Canada, Canary Islands, Italy
    */

    """,
    "maritime.berth_reference":"""
        -- maritime.berth_reference 港口泊位基础数据表：记录了全球各港口泊位的详细信息，包括地理位置、类型、货物处理能力等关键数据
        -- 注意: 已经确认的泊位信息是可用的
        CREATE TABLE maritime.berth_reference (
            "berth_uuid" varchar NOT NULL,      -- 泊位唯一标识符，用于唯一识别每个泊位
            "berth_type" varchar,               -- 泊位类型，如集装箱泊位、散货泊位、液体散货泊位等[可选值: '100', '120', '140', '160', '260', '800', '810']
            "load_type" varchar,                -- 装卸标识，表示泊位的主要功能：0-未知，1-装货，2-卸货，3-装卸货，[可选值: '0', '1', '2', '3']
            "cargo_type" varchar,               -- 货物类型，指明泊位主要处理的货物种类，如原油、煤炭、集装箱等[可选值: 'COAL', 'IRON_ORE', 'STEEL', 'CEMENT', 'SAND', 'CRUDE_OIL', 'LNG', 'LPG', 'GRAIN', 'SUGAR', 'BAUXITE', 'TIMBER', 'VEHICLES', 'CNTR']
            "port_code" varchar,                -- 关联港口代码，用于将泊位与其所属港口关联
            "name_en" varchar,                  -- 泊位英文名称
            "name_cn" varchar,                  -- 泊位中文名称
            "line_type" smallint,               -- 泊位几何类型：0-多边形（如港池），1-线性（如码头前沿），2-风电场[可选值: 0, 1, 2]
            "berth_line" varchar,               -- 泊位位置线，以经纬度点序列表示，格式：经度1 纬度1,经度2 纬度2,...
            "berth_line_geo" public.geography,  -- 泊位位置线的地理信息数据，用于地理空间分析和可视化
            "is_confirmed" smallint NOT NULL DEFAULT 0, -- 泊位信息确认状态：0-未确认，1-已确认. 仅有泊位状态为1的数据可用.[可选值: 0, 1]
            "berth_line_start_point" varchar,   -- 泊位起点坐标
            "berth_line_end_point" varchar,     -- 泊位终点坐标
            "start_lon" numeric(11,6),          -- 泊位起点经度
            "start_lat" numeric(11,6),          -- 泊位起点纬度
            "end_lon" numeric(11,6),            -- 泊位终点经度
            "end_lat" numeric(11,6),            -- 泊位终点纬度
            "berth_id" varchar,                 -- 泊位ID
            "center_lon" numeric(11,6),         -- STS（船对船）作业区域中心点经度，用于定位大型船舶停泊区
            "center_lat" numeric(11,6),         -- STS（船对船）作业区域中心点纬度，用于定位大型船舶停泊区
            "vessel_type" varchar,              -- 区域适用船型（一级分类），多个船型用逗号分隔[可选值: '10000', '20000', '30000', '40000', '50000', '60000']
            "is_build" smallint NOT NULL DEFAULT 0, -- 泊位类型：0-其他泊位，1-可建船泊位[可选值: 0, 1]
            PRIMARY KEY ("berth_uuid")
        );
        -- maritime.berth_reference 样例数据:
        /*
        Columns in maritime.berth_reference and 3 examples in each column for the high cardinality columns:
            berth_uuid(varchar): SYNTHETIC_BERTH_001, SYNTHETIC_BERTH_002, SYNTHETIC_BERTH_003
            port_code(varchar): SAMPLE_PORT_A, SAMPLE_PORT_B, SAMPLE_PORT_C
            name_en(varchar): Sample Container Berth, Sample STS Berth, Sample Tank Berth
            name_cn(varchar): 示例集装箱泊位, 示例STS泊位, 示例液散泊位
            berth_line(varchar): "10.000000 20.000000,10.010000 20.010000", "30.000000 40.000000,30.010000 40.010000", "50.000000 60.000000,50.010000 60.010000"
            berth_line_geo(public.geography): ANONYMIZED_GEOGRAPHY_01, ANONYMIZED_GEOGRAPHY_02, ANONYMIZED_GEOGRAPHY_03
            berth_line_start_point(varchar): 10.000000 20.000000, 30.000000 40.000000, 50.000000 60.000000
            berth_line_end_point(varchar): 10.010000 20.010000, 30.010000 40.010000, 50.010000 60.010000
            start_lon(numeric(11,6)): 10.000000, 30.000000, 50.000000
            start_lat(numeric(11,6)): 20.000000, 40.000000, 60.000000
            end_lon(numeric(11,6)): 10.010000, 30.010000, 50.010000
            end_lat(numeric(11,6)): 20.010000, 40.010000, 60.010000
            berth_id(varchar): SAMPLE_001, SAMPLE_002, SAMPLE_003
            center_lon(numeric(11,6)): 10.005000, 30.005000, 50.005000
            center_lat(numeric(11,6)): 20.005000, 40.005000, 60.005000
        */
        """,
    "maritime.port_efficiency_snapshot":"""
    -- port_efficiency_snapshot 港口运营效率即时记录表 ：
    -- 最新时间的记录和分析港口运营效率的关键指标，为航运业决策提供数据支持
    CREATE TABLE maritime.port_efficiency_snapshot (
        "port_code"              varchar,                     -- 港口唯一标识码，用于区分不同港口
        "summary_time"           timestamp with time zone,    -- 数据统计的具体时间点，格式 YYYY-MM-DD HH:MM:SS+TZ 精确到秒，包含时区信息
        "year_month_day_hour"    varchar,                     -- 数据统计时间的小时粒度，格式：YYYY-MM-DD-HH，便于按小时聚合分析
        "year_month_day"         varchar,                     -- 数据统计时间的日期粒度，格式：YYYY-MM-DD，用于日报表生成
        "year_month"             varchar,                     -- 数据统计时间的月份粒度，格式：YYYY-MM，用于月度趋势分析
        "year"                   varchar,                     -- 数据统计时间的年份，格式：YYYY，用于年度对比分析
        "vessel_type"            varchar,                     -- 船舶主要类型代码[可选值: '10000', '20000', '30000', '40000', '50000', '60000']
        "vessel_sub_type"        varchar,                     -- 船舶次级类型代码[可选值: '10200', '10400', '10600', '10800', '10900', '20300', '20500', '20600', '30100', '30300', '30600', '30700', '30800', '30820', '30830', '30840', '30850', '30900', '31000', '40400', '50100', '50200', '50300', '50400', '60300', '60400', '60500', '60700', '60820', '60830', '60900', '60910', '60920', '60930', '60950', '60970', '70000', '70200', '70300', '70500', '90000']
        "vessel_sub2_type"       varchar,                     -- 船舶第三级类型代码[可选值: '20501', '20502', '20503', '20504', '20506', '20508', '30101', '30301', '30601', '30701', '30102', '30302', '30602', '30702', '30103', '30303', '30603', '30703', '30104', '30304', '30604', '30704', '30105', '30305', '30605', '30106', '30306', '30606', '30801', '30901', '30802', '30902', '30821', '30831', '30822', '30832', '30823', '30833', '30824', '30834', '30825', '30835', '30826', '30836', '31001', '31002', '31003', '31004', '31005', '20302', '20304', '20306', '20308', '20310', '40401', '40402', '40403', '40404', '40405', '40406', '40407', '90010', '90020', '90030']
        "moor_num"               integer,                     -- 采样时刻锚地停泊的船舶数量，反映港口锚地使用情况
        "berth_num"              integer,                     -- 采样时刻靠泊的船舶数量，反映港口泊位使用情况
        "moor_dwt"               integer,                     -- 采样时刻锚地停泊船舶的总载重吨，衡量锚地停泊船舶规模
        "berth_dwt"              bigint,                      -- 采样时刻靠泊船舶的总载重吨，衡量靠泊船舶规模
        "average_moor_duration"  numeric(11,2),               -- 近7天内完成靠泊的船舶平均等泊时间(小时)，反映港口拥堵程度
        "average_berth_duration" numeric(11,2),               -- 近7天内完成锚泊的船舶平均作业时间(小时)，反映港口作业效率
        "average_stay_duration"  numeric(11,2),               -- 近7天内完成靠泊的船舶平均停留时间(小时)，反映港口整体周转效率
        "update_time"            timestamp with time zone,    -- 数据最后更新时间，格式：YYYY-MM-DD HH:MM:SS.SSSSSS+TZ 包含时区信息，用于追踪数据更新状态
        "stay_num"               integer,                     -- 采样时刻在港船舶总数，包括锚地和泊位的船舶，反映港口总体繁忙程度
        "stay_dwt"               integer,                     -- 采样时刻在港船舶总载重吨，反映在港船舶整体规模
        "moor_duration"          numeric(11,2),               -- 采样时刻锚地船舶的平均锚泊时长(小时)，反映当前锚地等待情况
        "berth_duration"         numeric(11,2),               -- 采样时刻靠泊船舶的平均靠泊时长(小时)，反映当前泊位作业情况
        "stay_duration"          numeric(11,2),               -- 采样时刻在港船舶的平均停留时长(小时)，反映当前港口整体效率
        "average_berth_num"      integer,                     -- 近7天内完成靠泊的船舶平均等泊数量，反映港口近期拥堵趋势
        "average_moor_num"       integer,                     -- 近7天内完成锚泊的船舶平均靠泊数量，反映港口近期作业量
        "average_stay_num"       integer,                     -- 近7天内完成靠泊的船舶平均停留数量，反映港口近期整体吞吐量
        "average_berth_dwt"      integer,                     -- 近7天内完成靠泊的船舶平均等泊载重吨，反映等泊船舶规模趋势
        "average_moor_dwt"       integer,                     -- 近7天内完成锚泊的船舶平均靠泊载重吨，反映作业船舶规模趋势
        "average_stay_dwt"       integer,                     -- 近7天内完成靠泊的船舶平均停留载重吨，反映整体船舶规模趋势
    ) PARTITION BY HASH ("port_code");

    /*
    Columns in maritime.port_efficiency_snapshot and 3 examples in each column for the high cardinality columns:
        port_code(varchar): USBEA, JPSTA, CNZHH
        summary_time(timestamp with time zone): 2024-10-21 08:00:00+08, 2020-04-27 12:00:00+08, 2020-01-02 04:00:00+08
        year_month_day_hour(varchar): 2024-10-21-08, 2020-04-27-12, 2020-01-02-04
        year_month_day(varchar): 2024-10-21, 2020-04-27, 2020-01-02
        year_month(varchar): 2024-10, 2020-04, 2020-01
        year(varchar): '2024', '2020', '2020'
        moor_num(integer): 0, 0, 0
        berth_num(integer): 1, 2, 0
        moor_dwt(integer): 0, 0, 0
        berth_dwt(bigint): 30383, 177738, 0
        average_moor_duration(numeric(11,2)): , 0.00, 0.00
        average_berth_duration(numeric(11,2)): 142.90, , 2.78
        average_stay_duration(numeric(11,2)): 142.90, , 2.78
        update_time(timestamp with time zone): 2024-10-21 08:03:38.928344+08, 2023-11-23 22:33:58.869264+08, 2024-06-18 14:51:26.099393+08
        stay_num(integer): 1, 2, 0
        stay_dwt(integer): 30383, 177738, 0
        moor_duration(numeric(11,2)): , , 
        berth_duration(numeric(11,2)): 171.15, 68.91, 
        stay_duration(numeric(11,2)): 171.15, 68.91, 
        average_berth_num(integer): 1, , 1
        average_moor_num(integer): , , 1
        average_stay_num(integer): 1, , 1
        average_berth_dwt(integer): 30386, , 938
        average_moor_dwt(integer): , , 938
        average_stay_dwt(integer): 30386, , 938

    */

    """,
    "maritime.port_efficiency_baseline":"""
    -- maritime.port_efficiency_baseline 港口效率七天平均值数据表：
    CREATE TABLE maritime.port_efficiency_baseline (
        "port_code" varchar,                -- 港口代码，用于唯一标识特定港口，如 CNDAL（大连）
        "vessel_type" varchar,              -- 船舶类型（一级分类）[可选值: '10000', '20000', '30000', '40000', '50000', '60000']
        "vessel_sub_type" varchar,          -- 船舶子类型（二级分类），进一步细分船舶类型[可选值: '10200', '10400', '10600', '10800', '10900', '20300', '20500', '20600', '30100', '30300', '30600', '30700', '30800', '30820', '30830', '30840', '30850', '30900', '31000', '40400', '50100', '50200', '50300', '50400', '60300', '60400', '60500', '60700', '60820', '60830', '60900', '60910', '60920', '60930', '60950', '60970', '70000', '70200', '70300', '70500', '90000']
        "vessel_sub2_type" varchar,         -- 船舶细分类型（三级分类），更精细的船舶分类[可选值: '20501', '20502', '20503', '20504', '20506', '20508', '30101', '30301', '30601', '30701', '30102', '30302', '30602', '30702', '30103', '30303', '30603', '30703', '30104', '30304', '30604', '30704', '30105', '30305', '30605', '30106', '30306', '30606', '30801', '30901', '30802', '30902', '30821', '30831', '30822', '30832', '30823', '30833', '30824', '30834', '30825', '30835', '30826', '30836', '31001', '31002', '31003', '31004', '31005', '20302', '20304', '20306', '20308', '20310', '40401', '40402', '40403', '40404', '40405', '40406', '40407', '90010', '90020', '90030']
        "moor_num" integer,                 -- 靠泊船舶数量，指在指定时间段内实际靠泊码头的船舶数量
        "berth_num" integer,                -- 等泊船舶数量，指在港口等待靠泊的船舶数量
        "moor_dwt" integer,                 -- 靠泊船舶总载重吨，所有靠泊船舶的载重吨之和
        "berth_dwt" integer,                -- 等泊船舶总载重吨，所有等泊船舶的载重吨之和
        "moor_duration" numeric(11,2),      -- 靠泊总时长（小时），所有船舶靠泊时间的累计
        "berth_duration" numeric(11,2),     -- 等泊总时长（小时），所有船舶等待靠泊时间的累计
        "stay_duration" numeric(11,2),      -- 停留总时长（小时），船舶在港口区域内停留的总时间，包括等泊和靠泊时间
        "stay_num" integer,                 -- 停留船舶数量，在港口区域内停留的总船舶数量
        "stay_dwt" integer,                 -- 停留船舶总载重吨，所有停留船舶的载重吨之和
        "average_stay_duration" numeric(11,2),  -- 平均停留时长（小时/艘），反映船舶在港口的平均停留效率
        "average_berth_duration" numeric(11,2), -- 平均等泊时长（小时/艘），反映港口的拥堵程度
        "average_moor_duration" numeric(11,2),  -- 平均靠泊时长（小时/艘），反映港口的装卸效率
        PRIMARY KEY ("uuid")
    );
    -- maritime.port_efficiency_baseline 样例数据:
    /*
    Columns in maritime.port_efficiency_baseline and 3 examples in each column for the high cardinality columns:
        port_code(varchar): CNDAL, CNDYI, SNDAK
        moor_num(integer): 0, 5, 2
        berth_num(integer): 1, 4, 1
        moor_dwt(integer): 0, 36689, 35854
        berth_dwt(integer): 108398, 30434, 11918
        moor_duration(numeric(11,2)): , 42.45, 31.66
        berth_duration(numeric(11,2)): 75.62, 16.65, 24.41
        stay_duration(numeric(11,2)): 75.62, 46.45, 42.65
        stay_num(integer): 1, 9, 4
        stay_dwt(integer): 108398, 67124, 47772
        average_stay_duration(numeric(11,2)): 157.61, 65.23, 61.42
        average_berth_duration(numeric(11,2)): 157.61, 27.73, 34.34
        average_moor_duration(numeric(11,2)): 0.00, 36.16, 25.45

    */

    """
}
