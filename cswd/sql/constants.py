"""
中英或科目映射
"""

BALANCESHEET_ITEM_MAPS = {'A001': '货币资金',
                          'A002': '结算备付金',
                          'A003': '拆出资金',
                          'A004': '交易性金融资产',
                          'A005': '衍生金融资产',
                          'A006': '应收票据',
                          'A007': '应收账款',
                          'A008': '预付款项',
                          'A009': '应收保费',
                          'A010': '应收分保账款',
                          'A011': '应收分保合同准备金',
                          'A012': '应收利息',
                          'A013': '应收股利',
                          'A014': '其他应收款',
                          'A015': '应收出口退税',
                          'A016': '应收补贴款',
                          'A017': '应收保证金',
                          'A018': '内部应收款',
                          'A019': '买入返售金融资产',
                          'A020': '存货',
                          'A021': '待摊费用',
                          'A022': '待处理流动资产损益',
                          'A023': '一年内到期的非流动资产',
                          'A024': '其他流动资产',
                          'A025': '流动资产合计',
                          'A026': '发放贷款及垫款',
                          'A027': '可供出售金融资产',
                          'A028': '持有至到期投资',
                          'A029': '长期应收款',
                          'A030': '长期股权投资',
                          'A031': '其他长期投资',
                          'A032': '投资性房地产',
                          'A033': '固定资产原值',
                          'A034': '累计折旧',
                          'A035': '固定资产净值',
                          'A036': '固定资产减值准备',
                          'A037': '固定资产',
                          'A038': '在建工程',
                          'A039': '工程物资',
                          'A040': '固定资产清理',
                          'A041': '生产性生物资产',
                          'A042': '公益性生物资产',
                          'A043': '油气资产',
                          'A044': '无形资产',
                          'A045': '开发支出',
                          'A046': '商誉',
                          'A047': '长期待摊费用',
                          'A048': '股权分置流通权',
                          'A049': '递延所得税资产',
                          'A050': '其他非流动资产',
                          'A051': '非流动资产合计',
                          'A052': '资产总计',
                          'A053': '短期借款',
                          'A054': '向中央银行借款',
                          'A055': '吸收存款及同业存放',
                          'A056': '拆入资金',
                          'A057': '交易性金融负债',
                          'A058': '衍生金融负债',
                          'A059': '应付票据',
                          'A060': '应付账款',
                          'A061': '预收账款',
                          'A062': '卖出回购金融资产款',
                          'A063': '应付手续费及佣金',
                          'A064': '应付职工薪酬',
                          'A065': '应交税费',
                          'A066': '应付利息',
                          'A067': '应付股利',
                          'A068': '其他应交款',
                          'A069': '应付保证金',
                          'A070': '内部应付款',
                          'A071': '其他应付款',
                          'A072': '预提费用',
                          'A073': '预计流动负债',
                          'A074': '应付分保账款',
                          'A075': '保险合同准备金',
                          'A076': '代理买卖证券款',
                          'A077': '代理承销证券款',
                          'A078': '国际票证结算',
                          'A079': '国内票证结算',
                          'A080': '递延收益',
                          'A081': '应付短期债券',
                          'A082': '一年内到期的非流动负债',
                          'A083': '其他流动负债',
                          'A084': '流动负债合计',
                          'A085': '长期借款',
                          'A086': '应付债券',
                          'A087': '长期应付款',
                          'A088': '专项应付款',
                          'A089': '预计非流动负债',
                          'A090': '长期递延收益',
                          'A091': '递延所得税负债',
                          'A092': '其他非流动负债',
                          'A093': '非流动负债合计',
                          'A094': '负债合计',
                          'A095': '实收资本或股本',
                          'A096': '资本公积',
                          'A097': '减库存股',
                          'A098': '专项储备',
                          'A099': '盈余公积',
                          'A100': '一般风险准备',
                          'A101': '未确定的投资损失',
                          'A102': '未分配利润',
                          'A103': '拟分配现金股利',
                          'A104': '外币报表折算差额',
                          'A105': '归属于母公司股东权益合计',
                          'A106': '少数股东权益',
                          'A107': '所有者权益或股东权益合计',
                          'A108': '负债和所有者权益或股东权益总计'}

PROFITSTATEMENT_ITEM_MAPS = {'A001': '营业总收入',
                             'A002': '营业收入',
                             'A003': '利息收入',
                             'A004': '已赚保费',
                             'A005': '手续费及佣金收入',
                             'A006': '房地产销售收入',
                             'A007': '其他业务收入',
                             'A008': '营业总成本',
                             'A009': '营业成本',
                             'A010': '利息支出',
                             'A011': '手续费及佣金支出',
                             'A012': '房地产销售成本',
                             'A013': '研发费用',
                             'A014': '退保金',
                             'A015': '赔付支出净额',
                             'A016': '提取保险合同准备金净额',
                             'A017': '保单红利支出',
                             'A018': '分保费用',
                             'A019': '其他业务成本',
                             'A020': '营业税金及附加',
                             'A021': '销售费用',
                             'A022': '管理费用',
                             'A023': '财务费用',
                             'A024': '资产减值损失',
                             'A025': '公允价值变动收益',
                             'A026': '投资收益',
                             'A027': '对联营企业和合营企业的投资收益',
                             'A028': '汇兑收益',
                             'A029': '期货损益',
                             'A030': '托管收益',
                             'A031': '补贴收入',
                             'A032': '其他业务利润',
                             'A033': '营业利润',
                             'A034': '营业外收入',
                             'A035': '营业外支出',
                             'A036': '非流动资产处置损失',
                             'A037': '利润总额',
                             'A038': '所得税费用',
                             'A039': '未确认投资损失',
                             'A040': '净利润',
                             'A041': '归属于母公司所有者的净利润',
                             'A042': '被合并方在合并前实现净利润',
                             'A043': '少数股东损益',
                             'A044': '基本每股收益',
                             'A045': '稀释每股收益'}

CASHFLOWSTATEMENT_ITEM_MAPS = {'A001': '销售商品及提供劳务收到的现金',
                               'A002': '客户存款和同业存放款项净增加额',
                               'A003': '向中央银行借款净增加额',
                               'A004': '向其他金融机构拆入资金净增加额',
                               'A005': '收到原保险合同保费取得的现金',
                               'A006': '收到再保险业务现金净额',
                               'A007': '保户储金及投资款净增加额',
                               'A008': '处置交易性金融资产净增加额',
                               'A009': '收取利息及手续费及佣金的现金',
                               'A010': '拆入资金净增加额',
                               'A011': '回购业务资金净增加额',
                               'A012': '收到的税费返还',
                               'A013': '收到的其他与经营活动有关的现金',
                               'A014': '经营活动现金流入小计',
                               'A015': '购买商品及接受劳务支付的现金',
                               'A016': '客户贷款及垫款净增加额',
                               'A017': '存放中央银行和同业款项净增加额',
                               'A018': '支付原保险合同赔付款项的现金',
                               'A019': '支付利息及手续费及佣金的现金',
                               'A020': '支付保单红利的现金',
                               'A021': '支付给职工以及为职工支付的现金',
                               'A022': '支付的各项税费',
                               'A023': '支付的其他与经营活动有关的现金',
                               'A024': '经营活动现金流出小计',
                               'A025': '经营活动产生的现金流量净额',
                               'A026': '收回投资所收到的现金',
                               'A027': '取得投资收益所收到的现金',
                               'A028': '处置固定资产及无形资产和其他长期资产所收回的现金净额',
                               'A029': '处置子公司及其他营业单位收到的现金净额',
                               'A030': '收到的其他与投资活动有关的现金',
                               'A031': '减少质押和定期存款所收到的现金',
                               'A032': '投资活动现金流入小计',
                               'A033': '购建固定资产及无形资产和其他长期资产所支付的现金',
                               'A034': '投资所支付的现金',
                               'A035': '质押贷款净增加额',
                               'A036': '取得子公司及其他营业单位支付的现金净额',
                               'A037': '支付的其他与投资活动有关的现金',
                               'A038': '增加质押和定期存款所支付的现金',
                               'A039': '投资活动现金流出小计',
                               'A040': '投资活动产生的现金流量净额',
                               'A041': '吸收投资收到的现金',
                               'A042': '其中子公司吸收少数股东投资收到的现金',
                               'A043': '取得借款收到的现金',
                               'A044': '发行债券收到的现金',
                               'A045': '收到其他与筹资活动有关的现金',
                               'A046': '筹资活动现金流入小计',
                               'A047': '偿还债务支付的现金',
                               'A048': '分配股利及利润或偿付利息所支付的现金',
                               'A049': '其中子公司支付给少数股东的股利及利润',
                               'A050': '支付其他与筹资活动有关的现金',
                               'A051': '筹资活动现金流出小计',
                               'A052': '筹资活动产生的现金流量净额',
                               'A053': '汇率变动对现金及现金等价物的影响',
                               'A054': '现金及现金等价物净增加额',
                               'A055': '加期初现金及现金等价物余额',
                               'A056': '期末现金及现金等价物余额',
                               'A057': '净利润',
                               'A058': '少数股东损益',
                               'A059': '未确认的投资损失',
                               'A060': '资产减值准备',
                               'A061': '固定资产折旧及油气资产折耗及生产性物资折旧',
                               'A062': '无形资产摊销',
                               'A063': '长期待摊费用摊销',
                               'A064': '待摊费用的减少',
                               'A065': '预提费用的增加',
                               'A066': '处置固定资产及无形资产和其他长期资产的损失',
                               'A067': '固定资产报废损失',
                               'A068': '公允价值变动损失',
                               'A069': '递延收益增加',
                               'A070': '预计负债',
                               'A071': '财务费用',
                               'A072': '投资损失',
                               'A073': '递延所得税资产减少',
                               'A074': '递延所得税负债增加',
                               'A075': '存货的减少',
                               'A076': '经营性应收项目的减少',
                               'A077': '经营性应付项目的增加',
                               'A078': '已完工尚未结算款的减少',
                               'A079': '已结算尚未完工款的增加',
                               'A080': '其他',
                               'A081': '经营活动产生现金流量净额',
                               'A082': '债务转为资本',
                               'A083': '一年内到期的可转换公司债券',
                               'A084': '融资租入固定资产',
                               'A085': '现金的期末余额',
                               'A086': '现金的期初余额',
                               'A087': '现金等价物的期末余额',
                               'A088': '现金等价物的期初余额',
                               'A089': '现金及现金等价物的净增加额'}

ZYZB_ITEM_MAPS = {'A001': '基本每股收益',
                  'A002': '每股净资产',
                  'A003': '每股经营活动产生的现金流量净额',
                  'A004': '主营业务收入',
                  'A005': '主营业务利润',
                  'A006': '营业利润',
                  'A007': '投资收益',
                  'A008': '营业外收支净额',
                  'A009': '利润总额',
                  'A010': '净利润',
                  'A011': '扣非净利润',
                  'A012': '经营活动产生的现金流量净额',
                  'A013': '现金及现金等价物净增加额',
                  'A014': '总资产',
                  'A015': '流动资产',
                  'A016': '总负债',
                  'A017': '流动负债',
                  'A018': '股东权益不含少数股东权益',
                  'A019': '净资产收益率加权'}

YLNL_ITEM_MAPS = {'A001': '总资产利润率',
                  'A002': '主营业务利润率',
                  'A003': '总资产净利润率',
                  'A004': '成本费用利润率',
                  'A005': '营业利润率',
                  'A006': '主营业务成本率',
                  'A007': '销售净利率',
                  'A008': '净资产收益率',
                  'A009': '股本报酬率',
                  'A010': '净资产报酬率',
                  'A011': '资产报酬率',
                  'A012': '销售毛利率',
                  'A013': '三项费用比重',
                  'A014': '非主营比重',
                  'A015': '主营利润比重'}

CHNL_ITEM_MAPS = {'A001': '流动比率',
                  'A002': '速动比率',
                  'A003': '现金比率',
                  'A004': '利息支付倍数',
                  'A005': '资产负债率',
                  'A006': '长期债务与营运资金比率',
                  'A007': '股东权益比率',
                  'A008': '长期负债比率',
                  'A009': '股东权益与固定资产比率',
                  'A010': '负债与所有者权益比率',
                  'A011': '长期资产与长期资金比率',
                  'A012': '资本化比率',
                  'A013': '固定资产净值率',
                  'A014': '资本固定化比率',
                  'A015': '产权比率',
                  'A016': '清算价值比率',
                  'A017': '固定资产比重'}

CZNL_ITEM_MAPS = {'A001': '主营业务收入增长率',
                  'A002': '净利润增长率',
                  'A003': '净资产增长率',
                  'A004': '总资产增长率'}

YYNL_ITEM_MAPS = {'A001': '应收账款周转率',
                  'A002': '应收账款周转天数',
                  'A003': '存货周转率',
                  'A004': '固定资产周转率',
                  'A005': '总资产周转率',
                  'A006': '存货周转天数',
                  'A007': '总资产周转天数',
                  'A008': '流动资产周转率',
                  'A009': '流动资产周转天数',
                  'A010': '经营现金净流量对销售收入比率',
                  'A011': '资产的经营现金流量回报率',
                  'A012': '经营现金净流量与净利润的比率',
                  'A013': '经营现金净流量对负债比率',
                  'A014': '现金流量比率'}

PERFORMANCEFORECAST_MAPS = {'A001': '股票简称',
                            'A002': '业绩预告类型',
                            'A003': '业绩预告摘要',
                            'A004': '净利润变动幅度',
                            'A005': '上年同期净利润'}

MARGIN_MAPS = {'A001': '融资余额',
               'A002': '融资买入额',
               'A003': '融资偿还额',
               'A004': '融券余量',
               'A005': '融券卖出量',
               'A006': '融券偿还量',
               'A007': '融券余量金额',
               'A008': '融券余额'}

ISSUE_MAPS = {'A001': '成立日期',
              'A002': '发行数量',
              'A003': '发行价格',
              'A004': '上市日期',
              'A005': '发行市盈率',
              'A006': '预计募资',
              'A007': '首日开盘价',
              'A008': '发行中签率',
              'A009': '实际募资',
              'A010': '主承销商',
              'A011': '上市保荐人',
              'A012': '历史沿革'}

QUOTATION_MAPS = {'A001': '时间',
                  'A002': '股票简称',
                  'A003': '开盘',
                  'A004': '前收盘',
                  'A005': '现价',
                  'A006': '最高',
                  'A007': '最低',
                  'A008': '竞买价',
                  'A009': '竞卖价',
                  'A010': '成交量',
                  'A011': '成交额',
                  'A012': '买1量',
                  'A013': '买1价',
                  'A014': '买2量',
                  'A015': '买2价',
                  'A016': '买3量',
                  'A017': '买3价',
                  'A018': '买4量',
                  'A019': '买4价',
                  'A020': '买5量',
                  'A021': '买5价',
                  'A022': '卖1量',
                  'A023': '卖1价',
                  'A024': '卖2量',
                  'A025': '卖2价',
                  'A026': '卖3量',
                  'A027': '卖3价',
                  'A028': '卖4量',
                  'A029': '卖4价',
                  'A030': '卖5量',
                  'A031': '卖5价'}

STOCKDAILY_MAPS = {'A001': '名称',
                   'A002': '开盘价',
                   'A003': '最高价',
                   'A004': '最低价',
                   'A005': '收盘价',
                   'A006': '成交量',
                   'A007': '成交金额',
                   'A008': '换手率',
                   'A009': '前收盘',
                   'A010': '涨跌额',
                   'A011': '涨跌幅',
                   'A012': '总市值',
                   'A013': '流通市值',
                   'A014': '成交笔数'}

DEALDETAIL_MAPS = {'A001': '时间',
                   'A002': '价格',
                   'A003': '涨跌额',
                   'A004': '成交量',
                   'A005': '成交额',
                   'A006': '方向'}

ST_MAPS = {'未上市': 'unlisted',
           '新上市': 'new',
           '实施特别处理': 'ST',
           '撤销特别处理': 'rescission',
           '实施其他特别处理': 'others',
           '换股上市': 'exchange',
           '暂停上市': 'PT',
           '恢复上市': 'resume',
           '终止上市': 'delisting'}