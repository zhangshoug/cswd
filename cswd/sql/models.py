import datetime

from sqlalchemy import (Column, Date, DateTime, Enum, Float, ForeignKey, Boolean,
                        Integer, SmallInteger, String, Text, func)
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship

from ..common.utils import to_table_name
from .base import Exchange, Plate, SpecialTreatmentType, Status, ShareholderType, Action


class CommonMixin(object):

    @declared_attr
    def __tablename__(cls):
        name = cls.__name__
        return to_table_name(name)

    last_updated = Column(DateTime,
                          default=datetime.datetime.now,
                          onupdate=datetime.datetime.now,
                          name='更新时间')

    id = Column(Integer,
                primary_key=True,
                autoincrement=True,
                name='序号')


class InvalidCode(Exception):
    """不合法股票代码"""
    pass


# 增强基本类
Base = declarative_base(cls=CommonMixin)


class Stock(Base):
    code = Column(String(6), unique=True, name='股票代码')
    name = Column(String(20), name='股票简称')
    latest_status = Column(Enum(Status), name='最新状态')

    def __repr__(self):
        return "<Stock(code='%s')>" % self.code

    @property
    def exchange(self):
        first_letter = self.code[0]
        if first_letter in ('6', ):
            return Exchange.SSE
        elif first_letter in ('0', '3'):
            return Exchange.SZSE
        else:
            raise InvalidCode('股票代码不合法！')

    @property
    def plate(self):
        if self.code[:3] == '002':
            return Plate.sme
        elif self.code[0] in ('3', ):
            return Plate.gem
        else:
            return Plate.main
    # 设定uselist=False指示一对一关系
    issue = relationship("Issue",
                         uselist=False,
                         back_populates="stock")


class Issue(Base):
    """发行信息"""
    A001_成立日期 = Column(Date, name='成立日期')
    A002_发行数量 = Column(Integer, name='发行数量')
    A003_发行价格 = Column(Float, name='发行价格')
    A004_上市日期 = Column(Date, name='上市日期')
    A005_发行市盈率 = Column(Float, name='发行市盈率')
    A006_预计募资 = Column(Float, name='预计募资')
    A007_首日开盘价 = Column(Float, name='首日开盘价')
    A008_发行中签率 = Column(Float, name='发行中签率')
    A009_实际募资 = Column(Float, name='实际募资')
    A010_主承销商 = Column(String, name='主承销商')
    A011_上市保荐人 = Column(String, name='上市保荐人')
    A012_历史沿革 = Column(Text, name='历史沿革')
    code = Column(String(6),
                  ForeignKey('stocks.股票代码'),
                  name='股票代码')
    stock = relationship("Stock", back_populates="issue")

    def __repr__(self):
        return "<Issue(code='%s',ipo='%s')>" % (self.code, self.A004_上市日期)


class TradingCalendar(Base):
    """交易日期"""
    date = Column(Date, unique=True, name='日期', index=True)
    is_trading = Column(Boolean, name='交易日')

    def __repr__(self):
        return "<TradingCalendar(date='%s')>" % self.date


class ShortName(Base):
    """股票简称历史记录"""
    # 外键规则：表名称.列名称
    code = Column(String(6),
                  ForeignKey('stocks.股票代码'),
                  index=True,
                  name='股票代码')
    date = Column(Date,
                  ForeignKey('trading_calendars.日期'),
                  index=True,
                  name='日期')
    short_name = Column(String,
                        nullable=False,
                        name='股票简称')
    memo = Column(String, name='备注说明')

    stock = relationship("Stock", back_populates="shortnames")

    def __repr__(self):
        fmt = "<ShortName(code='{}',name='{}',date='{}')>"
        return fmt.format(self.code, self.short_name, self.date)


Stock.shortnames = relationship("ShortName",
                                order_by=ShortName.date,
                                back_populates="stock")


class SpecialTreatment(Base):
    """股票特殊处理历史记录"""
    code = Column(String(6),
                  ForeignKey('stocks.股票代码'),
                  index=True,
                  name='股票代码')
    date = Column(Date,
                  ForeignKey('trading_calendars.日期'),
                  index=True,
                  name='日期')
    # 以枚举代替 0~9之间
    treatment = Column(Enum(SpecialTreatmentType), nullable=False, name='特别处理')
    memo = Column(String, name='备注说明')

    stock = relationship("Stock",
                         back_populates="specialtreatments")

    def __repr__(self):
        fmt = "<SpecialTreatment(code='%s',treatment='%s',date='%s')>"
        return fmt % (self.code, self.treatment, self.date)


Stock.specialtreatments = relationship("SpecialTreatment",
                                       order_by=SpecialTreatment.date,
                                       back_populates="stock")


class Shareholder(Base):
    """股东历史记录"""
    code = Column(String(6),
                  ForeignKey('stocks.股票代码'),
                  index=True,
                  name='股票代码')
    date = Column(Date,
                  ForeignKey('trading_calendars.日期'),
                  index=True,
                  name='日期')
    A001_股东类型 = Column(Enum(ShareholderType), name='股东类型')
    A002_内部序号 = Column(Integer, name='内部序号')
    A003_股东简称 = Column(String, name='股东简称')
    A004_持仓市值 = Column(Integer, name='持仓市值')
    A005_持仓数量 = Column(Integer, name='持仓数量')
    A006_与上期持仓股数变化 = Column(String, name='与上期持仓股数变化')
    A007_占基金净值比例 = Column(Float, name='占基金净值比例')
    A008_占流通股比例 = Column(Float, name='占流通股比例')
    stock = relationship("Stock", back_populates="shareholders")


Stock.shareholders = relationship("Shareholder",
                                  order_by=Shareholder.date,
                                  back_populates="stock")


class StockDaily(Base):
    """股票日线数据"""
    code = Column(String(6),
                  ForeignKey('stocks.股票代码'),
                  index=True,
                  name='股票代码')
    date = Column(Date,
                  ForeignKey('trading_calendars.日期'),
                  index=True,
                  name='日期')
    A001_名称 = Column(String,
                     nullable=False,
                     name='名称')
    A002_开盘价 = Column(Float, name='开盘价')
    A003_最高价 = Column(Float, name='最高价')
    A004_最低价 = Column(Float, name='最低价')
    A005_收盘价 = Column(Float, name='收盘价')
    A006_成交量 = Column(Integer, name='成交量')
    A007_成交金额 = Column(Float, name='成交金额')
    A008_换手率 = Column(Float, name='换手率')
    A009_前收盘 = Column(Float, name='前收盘')
    A010_涨跌额 = Column(Float, name='涨跌额')
    A011_涨跌幅 = Column(Float, name='涨跌幅')
    A012_总市值 = Column(Float, name='总市值')
    A013_流通市值 = Column(Float, name='流通市值')
    A014_成交笔数 = Column(Float, name='成交笔数')

    stock = relationship("Stock", back_populates="dailies")
    tdate = relationship("TradingCalendar", back_populates="dailies")


Stock.dailies = relationship("StockDaily",
                             order_by=StockDaily.date,
                             back_populates="stock")

TradingCalendar.dailies = relationship("StockDaily",
                                       order_by=StockDaily.code,
                                       back_populates="tdate")


class Category(Base):
    """基础分类"""
    code = Column(String, unique=True, name='类别编码')
    label = Column(String, name='分类')
    url = Column(String, name='网址')
    title = Column(String, name='名称')


class StockCategory(Base):
    """股票分类"""
    category_code = Column(String,
                           ForeignKey('categories.类别编码'),
                           index=True,
                           name='类别编码')
    stock_code = Column(String(6),
                        ForeignKey('stocks.股票代码'),
                        index=True,
                        name='股票代码')

    stock = relationship("Stock", back_populates="categories")
    category = relationship("Category", back_populates="stock_codes")


Category.stock_codes = relationship("StockCategory",
                                    order_by=StockCategory.stock_code,
                                    back_populates="category")

Stock.categories = relationship("StockCategory",
                                order_by=StockCategory.category_code,
                                back_populates="stock")

# 财务类


class BalanceSheet(Base):
    """
    资产负债表

    说明：
        1. 报告日期为定期报告的截止日期
        2. 公告日期为发布报告日期
        3. 如存在修订，则只保存最后一期数据，即修正后版本
    """
    code = Column(String,
                  ForeignKey('stocks.股票代码'),
                  index=True,
                  name='股票代码')
    date = Column(Date,
                  ForeignKey('trading_calendars.日期'),
                  index=True,
                  name='报告日期')
    announcement_date = Column(Date, name='公告日期')

    A001_货币资金 = Column(Float, name='货币资金')
    A002_结算备付金 = Column(Float, name='结算备付金')
    A003_拆出资金 = Column(Float, name='拆出资金')
    A004_交易性金融资产 = Column(Float, name='交易性金融资产')
    A005_衍生金融资产 = Column(Float, name='衍生金融资产')
    A006_应收票据 = Column(Float, name='应收票据')
    A007_应收账款 = Column(Float, name='应收账款')
    A008_预付款项 = Column(Float, name='预付款项')
    A009_应收保费 = Column(Float, name='应收保费')
    A010_应收分保账款 = Column(Float, name='应收分保账款')    # 10

    A011_应收分保合同准备金 = Column(Float, name='应收分保合同准备金')
    A012_应收利息 = Column(Float, name='应收利息')
    A013_应收股利 = Column(Float, name='应收股利')
    A014_其他应收款 = Column(Float, name='其他应收款')
    A015_应收出口退税 = Column(Float, name='应收出口退税')
    A016_应收补贴款 = Column(Float, name='应收补贴款')
    A017_应收保证金 = Column(Float, name='应收保证金')
    A018_内部应收款 = Column(Float, name='内部应收款')
    A019_买入返售金融资产 = Column(Float, name='买入返售金融资产')
    A020_存货 = Column(Float, name='存货')    # 20

    A021_待摊费用 = Column(Float, name='待摊费用')
    A022_待处理流动资产损益 = Column(Float, name='待处理流动资产损益')
    A023_一年内到期的非流动资产 = Column(Float, name='一年内到期的非流动资产')
    A024_其他流动资产 = Column(Float, name='其他流动资产')
    A025_流动资产合计 = Column(Float, name='流动资产合计')
    A026_发放贷款及垫款 = Column(Float, name='发放贷款及垫款')
    A027_可供出售金融资产 = Column(Float, name='可供出售金融资产')
    A028_持有至到期投资 = Column(Float, name='持有至到期投资')
    A029_长期应收款 = Column(Float, name='长期应收款')
    A030_长期股权投资 = Column(Float, name='长期股权投资')    # 30

    A031_其他长期投资 = Column(Float, name='其他长期投资')
    A032_投资性房地产 = Column(Float, name='投资性房地产')
    A033_固定资产原值 = Column(Float, name='固定资产原值')
    A034_累计折旧 = Column(Float, name='累计折旧')
    A035_固定资产净值 = Column(Float, name='固定资产净值')
    A036_固定资产减值准备 = Column(Float, name='固定资产减值准备')
    A037_固定资产 = Column(Float, name='固定资产')
    A038_在建工程 = Column(Float, name='在建工程')
    A039_工程物资 = Column(Float, name='工程物资')
    A040_固定资产清理 = Column(Float, name='固定资产清理')    # 40

    A041_生产性生物资产 = Column(Float, name='生产性生物资产')
    A042_公益性生物资产 = Column(Float, name='公益性生物资产')
    A043_油气资产 = Column(Float, name='油气资产')
    A044_无形资产 = Column(Float, name='无形资产')
    A045_开发支出 = Column(Float, name='开发支出')
    A046_商誉 = Column(Float, name='商誉')
    A047_长期待摊费用 = Column(Float, name='长期待摊费用')
    A048_股权分置流通权 = Column(Float, name='股权分置流通权')
    A049_递延所得税资产 = Column(Float, name='递延所得税资产')
    A050_其他非流动资产 = Column(Float, name='其他非流动资产')    # 50

    A051_非流动资产合计 = Column(Float, name='非流动资产合计')
    A052_资产总计 = Column(Float, name='资产总计')
    A053_短期借款 = Column(Float, name='短期借款')
    A054_向中央银行借款 = Column(Float, name='向中央银行借款')
    A055_吸收存款及同业存放 = Column(Float, name='吸收存款及同业存放')
    A056_拆入资金 = Column(Float, name='拆入资金')
    A057_交易性金融负债 = Column(Float, name='交易性金融负债')
    A058_衍生金融负债 = Column(Float, name='衍生金融负债')
    A059_应付票据 = Column(Float, name='应付票据')
    A060_应付账款 = Column(Float, name='应付账款')    # 60

    A061_预收账款 = Column(Float, name='预收账款')
    A062_卖出回购金融资产款 = Column(Float, name='卖出回购金融资产款')
    A063_应付手续费及佣金 = Column(Float, name='应付手续费及佣金')
    A064_应付职工薪酬 = Column(Float, name='应付职工薪酬')
    A065_应交税费 = Column(Float, name='应交税费')
    A066_应付利息 = Column(Float, name='应付利息')
    A067_应付股利 = Column(Float, name='应付股利')
    A068_其他应交款 = Column(Float, name='其他应交款')
    A069_应付保证金 = Column(Float, name='应付保证金')
    A070_内部应付款 = Column(Float, name='内部应付款')    # 70

    A071_其他应付款 = Column(Float, name='其他应付款')
    A072_预提费用 = Column(Float, name='预提费用')
    A073_预计流动负债 = Column(Float, name='预计流动负债')
    A074_应付分保账款 = Column(Float, name='应付分保账款')
    A075_保险合同准备金 = Column(Float, name='保险合同准备金')
    A076_代理买卖证券款 = Column(Float, name='代理买卖证券款')
    A077_代理承销证券款 = Column(Float, name='代理承销证券款')
    A078_国际票证结算 = Column(Float, name='国际票证结算')
    A079_国内票证结算 = Column(Float, name='国内票证结算')
    A080_递延收益 = Column(Float, name='递延收益')    # 80

    A081_应付短期债券 = Column(Float, name='应付短期债券')
    A082_一年内到期的非流动负债 = Column(Float, name='一年内到期的非流动负债')
    A083_其他流动负债 = Column(Float, name='其他流动负债')
    A084_流动负债合计 = Column(Float, name='流动负债合计')
    A085_长期借款 = Column(Float, name='长期借款')
    A086_应付债券 = Column(Float, name='应付债券')
    A087_长期应付款 = Column(Float, name='长期应付款')
    A088_专项应付款 = Column(Float, name='专项应付款')
    A089_预计非流动负债 = Column(Float, name='预计非流动负债')
    A090_长期递延收益 = Column(Float, name='长期递延收益')    # 90

    A091_递延所得税负债 = Column(Float, name='递延所得税负债')
    A092_其他非流动负债 = Column(Float, name='其他非流动负债')
    A093_非流动负债合计 = Column(Float, name='非流动负债合计')
    A094_负债合计 = Column(Float, name='负债合计')
    A095_实收资本或股本 = Column(Float, name='实收资本或股本')
    A096_资本公积 = Column(Float, name='资本公积')
    A097_减库存股 = Column(Float, name='减库存股')
    A098_专项储备 = Column(Float, name='专项储备')
    A099_盈余公积 = Column(Float, name='盈余公积')
    A100_一般风险准备 = Column(Float, name='一般风险准备')    # 100

    A101_未确定的投资损失 = Column(Float, name='未确定的投资损失')
    A102_未分配利润 = Column(Float, name='未分配利润')
    A103_拟分配现金股利 = Column(Float, name='拟分配现金股利')
    A104_外币报表折算差额 = Column(Float, name='外币报表折算差额')
    A105_归属于母公司股东权益合计 = Column(Float, name='归属于母公司股东权益合计')
    A106_少数股东权益 = Column(Float, name='少数股东权益')
    A107_所有者权益或股东权益合计 = Column(Float, name='所有者权益或股东权益合计')
    A108_负债和所有者权益或股东权益总计 = Column(Float, name='负债和所有者权益或股东权益总计')   # 108

    stock = relationship("Stock", back_populates="balance_sheet")


Stock.balance_sheet = relationship("BalanceSheet",
                                   order_by=BalanceSheet.date,
                                   back_populates="stock")


class ProfitStatement(Base):
    """
    利润表

    说明：
        1. 报告日期为定期报告的截止日期
        2. 公告日期为发布报告日期
        3. 如存在修订，则只保存最后一期数据，即修正后版本
    """
    code = Column(String,
                  ForeignKey('stocks.股票代码'),
                  index=True,
                  name='股票代码')
    date = Column(Date,
                  ForeignKey('trading_calendars.日期'),
                  index=True,
                  name='报告日期')
    announcement_date = Column(Date, name='公告日期')

    A001_营业总收入 = Column(Float, name='营业总收入')
    A002_营业收入 = Column(Float, name='营业收入')
    A003_利息收入 = Column(Float, name='利息收入')
    A004_已赚保费 = Column(Float, name='已赚保费')
    A005_手续费及佣金收入 = Column(Float, name='手续费及佣金收入')
    A006_房地产销售收入 = Column(Float, name='房地产销售收入')
    A007_其他业务收入 = Column(Float, name='其他业务收入')
    A008_营业总成本 = Column(Float, name='营业总成本')
    A009_营业成本 = Column(Float, name='营业成本')
    A010_利息支出 = Column(Float, name='利息支出')  # 10

    A011_手续费及佣金支出 = Column(Float, name='手续费及佣金支出')
    A012_房地产销售成本 = Column(Float, name='房地产销售成本')
    A013_研发费用 = Column(Float, name='研发费用')
    A014_退保金 = Column(Float, name='退保金')
    A015_赔付支出净额 = Column(Float, name='赔付支出净额')
    A016_提取保险合同准备金净额 = Column(Float, name='提取保险合同准备金净额')
    A017_保单红利支出 = Column(Float, name='保单红利支出')
    A018_分保费用 = Column(Float, name='分保费用')
    A019_其他业务成本 = Column(Float, name='其他业务成本')
    A020_营业税金及附加 = Column(Float, name='营业税金及附加')  # 20

    A021_销售费用 = Column(Float, name='销售费用')
    A022_管理费用 = Column(Float, name='管理费用')
    A023_财务费用 = Column(Float, name='财务费用')
    A024_资产减值损失 = Column(Float, name='资产减值损失')
    A025_公允价值变动收益 = Column(Float, name='公允价值变动收益')
    A026_投资收益 = Column(Float, name='投资收益')
    A027_对联营企业和合营企业的投资收益 = Column(Float, name='对联营企业和合营企业的投资收益')
    A028_汇兑收益 = Column(Float, name='汇兑收益')
    A029_期货损益 = Column(Float, name='期货损益')
    A030_托管收益 = Column(Float, name='托管收益')  # 30

    A031_补贴收入 = Column(Float, name='补贴收入')
    A032_其他业务利润 = Column(Float, name='其他业务利润')
    A033_营业利润 = Column(Float, name='营业利润')
    A034_营业外收入 = Column(Float, name='营业外收入')
    A035_营业外支出 = Column(Float, name='营业外支出')
    A036_非流动资产处置损失 = Column(Float, name='非流动资产处置损失')
    A037_利润总额 = Column(Float, name='利润总额')
    A038_所得税费用 = Column(Float, name='所得税费用')
    A039_未确认投资损失 = Column(Float, name='未确认投资损失')
    A040_净利润 = Column(Float, name='净利润')  # 40

    A041_归属于母公司所有者的净利润 = Column(Float, name='归属于母公司所有者的净利润')
    A042_被合并方在合并前实现净利润 = Column(Float, name='被合并方在合并前实现净利润')
    A043_少数股东损益 = Column(Float, name='少数股东损益')
    A044_基本每股收益 = Column(Float, name='基本每股收益')
    A045_稀释每股收益 = Column(Float, name='稀释每股收益')  # 45

    stock = relationship("Stock", back_populates="profit_statements")


Stock.profit_statements = relationship("ProfitStatement",
                                       order_by=ProfitStatement.date,
                                       back_populates="stock")


class CashflowStatement(Base):
    """
    现金流量表

    说明：
        1. 报告日期为定期报告的截止日期
        2. 公告日期为发布报告日期
        3. 如存在修订，则只保存最后一期数据，即修正后版本
    """
    code = Column(String,
                  ForeignKey('stocks.股票代码'),
                  index=True,
                  name='股票代码')
    date = Column(Date,
                  ForeignKey('trading_calendars.日期'),
                  index=True,
                  name='报告日期')
    announcement_date = Column(Date, name='公告日期')

    A001_销售商品及提供劳务收到的现金 = Column(Float, name='销售商品及提供劳务收到的现金')
    A002_客户存款和同业存放款项净增加额 = Column(Float, name='客户存款和同业存放款项净增加额')
    A003_向中央银行借款净增加额 = Column(Float, name='向中央银行借款净增加额')
    A004_向其他金融机构拆入资金净增加额 = Column(Float, name='向其他金融机构拆入资金净增加额')
    A005_收到原保险合同保费取得的现金 = Column(Float, name='收到原保险合同保费取得的现金')
    A006_收到再保险业务现金净额 = Column(Float, name='收到再保险业务现金净额')
    A007_保户储金及投资款净增加额 = Column(Float, name='保户储金及投资款净增加额')
    A008_处置交易性金融资产净增加额 = Column(Float, name='处置交易性金融资产净增加额')
    A009_收取利息及手续费及佣金的现金 = Column(Float, name='收取利息及手续费及佣金的现金')
    A010_拆入资金净增加额 = Column(Float, name='拆入资金净增加额')  # 10

    A011_回购业务资金净增加额 = Column(Float, name='回购业务资金净增加额')
    A012_收到的税费返还 = Column(Float, name='收到的税费返还')
    A013_收到的其他与经营活动有关的现金 = Column(Float, name='收到的其他与经营活动有关的现金')
    A014_经营活动现金流入小计 = Column(Float, name='经营活动现金流入小计')
    A015_购买商品及接受劳务支付的现金 = Column(Float, name='购买商品及接受劳务支付的现金')
    A016_客户贷款及垫款净增加额 = Column(Float, name='客户贷款及垫款净增加额')
    A017_存放中央银行和同业款项净增加额 = Column(Float, name='存放中央银行和同业款项净增加额')
    A018_支付原保险合同赔付款项的现金 = Column(Float, name='支付原保险合同赔付款项的现金')
    A019_支付利息及手续费及佣金的现金 = Column(Float, name='支付利息及手续费及佣金的现金')
    A020_支付保单红利的现金 = Column(Float, name='支付保单红利的现金')  # 20

    A021_支付给职工以及为职工支付的现金 = Column(Float, name='支付给职工以及为职工支付的现金')
    A022_支付的各项税费 = Column(Float, name='支付的各项税费')
    A023_支付的其他与经营活动有关的现金 = Column(Float, name='支付的其他与经营活动有关的现金')
    A024_经营活动现金流出小计 = Column(Float, name='经营活动现金流出小计')
    A025_经营活动产生的现金流量净额 = Column(Float, name='经营活动产生的现金流量净额')
    A026_收回投资所收到的现金 = Column(Float, name='收回投资所收到的现金')
    A027_取得投资收益所收到的现金 = Column(Float, name='取得投资收益所收到的现金')
    A028_处置固定资产及无形资产和其他长期资产所收回的现金净额 = Column(
        Float, name='处置固定资产及无形资产和其他长期资产所收回的现金净额')
    A029_处置子公司及其他营业单位收到的现金净额 = Column(Float, name='处置子公司及其他营业单位收到的现金净额')
    A030_收到的其他与投资活动有关的现金 = Column(Float, name='收到的其他与投资活动有关的现金')  # 30

    A031_减少质押和定期存款所收到的现金 = Column(Float, name='减少质押和定期存款所收到的现金')
    A032_投资活动现金流入小计 = Column(Float, name='投资活动现金流入小计')
    A033_购建固定资产及无形资产和其他长期资产所支付的现金 = Column(
        Float, name='购建固定资产及无形资产和其他长期资产所支付的现金')
    A034_投资所支付的现金 = Column(Float, name='投资所支付的现金')
    A035_质押贷款净增加额 = Column(Float, name='质押贷款净增加额')
    A036_取得子公司及其他营业单位支付的现金净额 = Column(Float, name='取得子公司及其他营业单位支付的现金净额')
    A037_支付的其他与投资活动有关的现金 = Column(Float, name='支付的其他与投资活动有关的现金')
    A038_增加质押和定期存款所支付的现金 = Column(Float, name='增加质押和定期存款所支付的现金')
    A039_投资活动现金流出小计 = Column(Float, name='投资活动现金流出小计')
    A040_投资活动产生的现金流量净额 = Column(Float, name='投资活动产生的现金流量净额')  # 40

    A041_吸收投资收到的现金 = Column(Float, name='吸收投资收到的现金')
    A042_其中子公司吸收少数股东投资收到的现金 = Column(Float, name='其中子公司吸收少数股东投资收到的现金')
    A043_取得借款收到的现金 = Column(Float, name='取得借款收到的现金')
    A044_发行债券收到的现金 = Column(Float, name='发行债券收到的现金')
    A045_收到其他与筹资活动有关的现金 = Column(Float, name='收到其他与筹资活动有关的现金')
    A046_筹资活动现金流入小计 = Column(Float, name='筹资活动现金流入小计')
    A047_偿还债务支付的现金 = Column(Float, name='偿还债务支付的现金')
    A048_分配股利及利润或偿付利息所支付的现金 = Column(Float, name='分配股利及利润或偿付利息所支付的现金')
    A049_其中子公司支付给少数股东的股利及利润 = Column(Float, name='其中子公司支付给少数股东的股利及利润')
    A050_支付其他与筹资活动有关的现金 = Column(Float, name='支付其他与筹资活动有关的现金')  # 50

    A051_筹资活动现金流出小计 = Column(Float, name='筹资活动现金流出小计')
    A052_筹资活动产生的现金流量净额 = Column(Float, name='筹资活动产生的现金流量净额')
    A053_汇率变动对现金及现金等价物的影响 = Column(Float, name='汇率变动对现金及现金等价物的影响')
    A054_现金及现金等价物净增加额 = Column(Float, name='现金及现金等价物净增加额')
    A055_加期初现金及现金等价物余额 = Column(Float, name='加期初现金及现金等价物余额')
    A056_期末现金及现金等价物余额 = Column(Float, name='期末现金及现金等价物余额')
    A057_净利润 = Column(Float, name='净利润')
    A058_少数股东损益 = Column(Float, name='少数股东损益')
    A059_未确认的投资损失 = Column(Float, name='未确认的投资损失')
    A060_资产减值准备 = Column(Float, name='资产减值准备')  # 60

    A061_固定资产折旧及油气资产折耗及生产性物资折旧 = Column(Float, name='固定资产折旧及油气资产折耗及生产性物资折旧')
    A062_无形资产摊销 = Column(Float, name='无形资产摊销')
    A063_长期待摊费用摊销 = Column(Float, name='长期待摊费用摊销')
    A064_待摊费用的减少 = Column(Float, name='待摊费用的减少')
    A065_预提费用的增加 = Column(Float, name='预提费用的增加')
    A066_处置固定资产及无形资产和其他长期资产的损失 = Column(Float, name='处置固定资产及无形资产和其他长期资产的损失')
    A067_固定资产报废损失 = Column(Float, name='固定资产报废损失')
    A068_公允价值变动损失 = Column(Float, name='公允价值变动损失')
    A069_递延收益增加 = Column(Float, name='递延收益增加')
    A070_预计负债 = Column(Float, name='预计负债')  # 70

    A071_财务费用 = Column(Float, name='财务费用')
    A072_投资损失 = Column(Float, name='投资损失')
    A073_递延所得税资产减少 = Column(Float, name='递延所得税资产减少')
    A074_递延所得税负债增加 = Column(Float, name='递延所得税负债增加')
    A075_存货的减少 = Column(Float, name='存货的减少')
    A076_经营性应收项目的减少 = Column(Float, name='经营性应收项目的减少')
    A077_经营性应付项目的增加 = Column(Float, name='经营性应付项目的增加')
    A078_已完工尚未结算款的减少 = Column(Float, name='已完工尚未结算款的减少')
    A079_已结算尚未完工款的增加 = Column(Float, name='已结算尚未完工款的增加')
    A080_其他 = Column(Float, name='其他')  # 80

    A081_经营活动产生现金流量净额 = Column(Float, name='经营活动产生现金流量净额')
    A082_债务转为资本 = Column(Float, name='债务转为资本')
    A083_一年内到期的可转换公司债券 = Column(Float, name='一年内到期的可转换公司债券')
    A084_融资租入固定资产 = Column(Float, name='融资租入固定资产')
    A085_现金的期末余额 = Column(Float, name='现金的期末余额')
    A086_现金的期初余额 = Column(Float, name='现金的期初余额')
    A087_现金等价物的期末余额 = Column(Float, name='现金等价物的期末余额')
    A088_现金等价物的期初余额 = Column(Float, name='现金等价物的期初余额')
    A089_现金及现金等价物的净增加额 = Column(Float, name='现金及现金等价物的净增加额')

    stock = relationship("Stock", back_populates="cashflow_statements")


Stock.cashflow_statements = relationship("CashflowStatement",
                                         order_by=CashflowStatement.date,
                                         back_populates="stock")


class ZYZB(Base):
    """
    主要财务指标

    说明：
        1. 报告日期为定期报告的截止日期
        2. 公告日期为发布报告日期
        3. 如存在修订，则只保存最后一期数据，即修正后版本
    """
    code = Column(String,
                  ForeignKey('stocks.股票代码'),
                  index=True,
                  name='股票代码')
    date = Column(Date,
                  ForeignKey('trading_calendars.日期'),
                  index=True,
                  name='报告日期')
    announcement_date = Column(Date, name='公告日期')

    # 主要财务指标
    A001_基本每股收益 = Column(Float, name='基本每股收益')
    A002_每股净资产 = Column(Float, name='每股净资产')
    A003_每股经营活动产生的现金流量净额 = Column(Float, name='每股经营活动产生的现金流量净额')
    A004_主营业务收入 = Column(Float, name='主营业务收入')
    A005_主营业务利润 = Column(Float, name='主营业务利润')
    A006_营业利润 = Column(Float, name='营业利润')
    A007_投资收益 = Column(Float, name='投资收益')
    A008_营业外收支净额 = Column(Float, name='营业外收支净额')
    A009_利润总额 = Column(Float, name='利润总额')
    A010_净利润 = Column(Float, name='净利润')  # 10

    A011_扣非净利润 = Column(Float, name='扣非净利润')
    A012_经营活动产生的现金流量净额 = Column(Float, name='经营活动产生的现金流量净额')
    A013_现金及现金等价物净增加额 = Column(Float, name='现金及现金等价物净增加额')
    A014_总资产 = Column(Float, name='总资产')
    A015_流动资产 = Column(Float, name='流动资产')
    A016_总负债 = Column(Float, name='总负债')
    A017_流动负债 = Column(Float, name='流动负债')
    A018_股东权益不含少数股东权益 = Column(Float, name='股东权益不含少数股东权益')
    A019_净资产收益率加权 = Column(Float, name='净资产收益率加权')  # 19

    stock = relationship("Stock", back_populates="zyzb")


Stock.zyzb = relationship("ZYZB",
                          order_by=ZYZB.date,
                          back_populates="stock")


class YLNL(Base):
    """
    盈利能力

    说明：
        1. 报告日期为定期报告的截止日期
        2. 公告日期为发布报告日期
        3. 如存在修订，则只保存最后一期数据，即修正后版本
    """
    code = Column(String,
                  ForeignKey('stocks.股票代码'),
                  index=True,
                  name='股票代码')
    date = Column(Date,
                  ForeignKey('trading_calendars.日期'),
                  index=True,
                  name='报告日期')
    announcement_date = Column(Date, name='公告日期')

    # 盈利能力
    A001_总资产利润率 = Column(Float, name='总资产利润率')
    A002_主营业务利润率 = Column(Float, name='主营业务利润率')
    A003_总资产净利润率 = Column(Float, name='总资产净利润率')
    A004_成本费用利润率 = Column(Float, name='成本费用利润率')
    A005_营业利润率 = Column(Float, name='营业利润率')
    A006_主营业务成本率 = Column(Float, name='主营业务成本率')
    A007_销售净利率 = Column(Float, name='销售净利率')
    A008_净资产收益率 = Column(Float, name='净资产收益率')
    A009_股本报酬率 = Column(Float, name='股本报酬率')
    A010_净资产报酬率 = Column(Float, name='净资产报酬率')  # 10

    A011_资产报酬率 = Column(Float, name='资产报酬率')
    A012_销售毛利率 = Column(Float, name='销售毛利率')
    A013_三项费用比重 = Column(Float, name='三项费用比重')
    A014_非主营比重 = Column(Float, name='非主营比重')
    A015_主营利润比重 = Column(Float, name='主营利润比重')  # 15

    stock = relationship("Stock", back_populates="ylnl")


Stock.ylnl = relationship("YLNL",
                          order_by=YLNL.date,
                          back_populates="stock")


class CHNL(Base):
    """
    偿还能力

    说明：
        1. 报告日期为定期报告的截止日期
        2. 公告日期为发布报告日期
        3. 如存在修订，则只保存最后一期数据，即修正后版本
    """
    code = Column(String,
                  ForeignKey('stocks.股票代码'),
                  index=True,
                  name='股票代码')
    date = Column(Date,
                  ForeignKey('trading_calendars.日期'),
                  index=True,
                  name='报告日期')
    announcement_date = Column(Date, name='公告日期')
    # 偿还能力
    A001_流动比率 = Column(Float, name='流动比率')
    A002_速动比率 = Column(Float, name='速动比率')
    A003_现金比率 = Column(Float, name='现金比率')
    A004_利息支付倍数 = Column(Float, name='利息支付倍数')
    A005_资产负债率 = Column(Float, name='资产负债率')
    A006_长期债务与营运资金比率 = Column(Float, name='长期债务与营运资金比率')
    A007_股东权益比率 = Column(Float, name='股东权益比率')
    A008_长期负债比率 = Column(Float, name='长期负债比率')
    A009_股东权益与固定资产比率 = Column(Float, name='股东权益与固定资产比率')
    A010_负债与所有者权益比率 = Column(Float, name='负债与所有者权益比率')  # 10

    A011_长期资产与长期资金比率 = Column(Float, name='长期资产与长期资金比率')
    A012_资本化比率 = Column(Float, name='资本化比率')
    A013_固定资产净值率 = Column(Float, name='固定资产净值率')
    A014_资本固定化比率 = Column(Float, name='资本固定化比率')
    A015_产权比率 = Column(Float, name='产权比率')
    A016_清算价值比率 = Column(Float, name='清算价值比率')
    A017_固定资产比重 = Column(Float, name='固定资产比重')  # 17

    stock = relationship("Stock", back_populates="chnl")


Stock.chnl = relationship("CHNL",
                          order_by=CHNL.date,
                          back_populates="stock")


class CZNL(Base):
    """
    成长能力

    说明：
        1. 报告日期为定期报告的截止日期
        2. 公告日期为发布报告日期
        3. 如存在修订，则只保存最后一期数据，即修正后版本
    """
    code = Column(String,
                  ForeignKey('stocks.股票代码'),
                  index=True,
                  name='股票代码')
    date = Column(Date,
                  ForeignKey('trading_calendars.日期'),
                  index=True,
                  name='报告日期')
    announcement_date = Column(Date, name='公告日期')
    # 成长指标
    A001_主营业务收入增长率 = Column(Float, name='主营业务收入增长率')
    A002_净利润增长率 = Column(Float, name='净利润增长率')
    A003_净资产增长率 = Column(Float, name='净资产增长率')
    A004_总资产增长率 = Column(Float, name='总资产增长率')

    stock = relationship("Stock", back_populates="cznl")


Stock.cznl = relationship("CZNL",
                          order_by=CZNL.date,
                          back_populates="stock")


class YYNL(Base):
    """
    营运能力

    说明：
        1. 报告日期为定期报告的截止日期
        2. 公告日期为发布报告日期
        3. 如存在修订，则只保存最后一期数据，即修正后版本
    """
    code = Column(String,
                  ForeignKey('stocks.股票代码'),
                  index=True,
                  name='股票代码')
    date = Column(Date,
                  ForeignKey('trading_calendars.日期'),
                  index=True,
                  name='报告日期')
    announcement_date = Column(Date, name='公告日期')
    # 营运能力
    A001_应收账款周转率 = Column(Float, name='应收账款周转率')
    A002_应收账款周转天数 = Column(Float, name='应收账款周转天数')
    A003_存货周转率 = Column(Float, name='存货周转率')
    A004_固定资产周转率 = Column(Float, name='固定资产周转率')
    A005_总资产周转率 = Column(Float, name='总资产周转率')
    A006_存货周转天数 = Column(Float, name='存货周转天数')
    A007_总资产周转天数 = Column(Float, name='总资产周转天数')
    A008_流动资产周转率 = Column(Float, name='流动资产周转率')
    A009_流动资产周转天数 = Column(Float, name='流动资产周转天数')
    A010_经营现金净流量对销售收入比率 = Column(Float, name='经营现金净流量对销售收入比率')  # 10

    A011_资产的经营现金流量回报率 = Column(Float, name='资产的经营现金流量回报率')
    A012_经营现金净流量与净利润的比率 = Column(Float, name='经营现金净流量与净利润的比率')
    A013_经营现金净流量对负债比率 = Column(Float, name='经营现金净流量对负债比率')
    A014_现金流量比率 = Column(Float, name='现金流量比率')  # 14

    stock = relationship("Stock", back_populates="yynl")


Stock.yynl = relationship("YYNL",
                          order_by=YYNL.date,
                          back_populates="stock")


class PerformanceForecast(Base):
    """业绩预告"""
    code = Column(String(6),
                  ForeignKey('stocks.股票代码'),
                  index=True,
                  name='股票代码')
    date = Column(Date,
                  #   ForeignKey('trading_calendars.日期'),
                  index=True,
                  name='公告日期')
    A001_股票简称 = Column(String, name='股票简称')
    A002_业绩预告类型 = Column(String, name='业绩预告类型')
    A003_业绩预告摘要 = Column(String, name='业绩预告摘要')
    A004_净利润变动幅度 = Column(String, name='净利润变动幅度')
    A005_上年同期净利润 = Column(Text, name='上年同期净利润')
    stock = relationship("Stock", back_populates="performance_forecast")


Stock.performance_forecast = relationship("PerformanceForecast",
                                          order_by=PerformanceForecast.date,
                                          back_populates="stock")

# 指数


class IndexInfo(Base):
    """股票指数信息"""
    code = Column(String, unique=True,
                  index=True, name='指数代码')
    title = Column(String, name='指数简称')
    url = Column(String, name='网址')
    origin_code = Column(String, unique=True, nullable=False, name='指数编码')


class IndexDaily(Base):
    """指数日线交易数据"""
    code = Column(String,
                  ForeignKey('index_infos.指数代码'),
                  index=True,
                  name='股票代码')
    date = Column(Date,
                  ForeignKey('trading_calendars.日期'),
                  index=True,
                  name='日期')
    open = Column(Float, name='开盘价')
    high = Column(Float, name='最高价')
    low = Column(Float, name='最低价')
    close = Column(Float, name='收盘价')
    volume = Column(Float, name='成交量')
    amount = Column(Float, name='成交额')
    change_pct = Column(Float, name='涨跌幅')


# 信息类


class GlobalNews(Base):
    """全球财经新闻"""
    mid = Column(DateTime, unique=True, name='内部序号')
    content = Column(Text, name='概要')
    pub_time = Column(String(8), name='发布时间')
    categories = Column(String(10), name='类别')

# 其他


class Treasury(Base):
    """国债资金成本"""
    date = Column(Date,
                  ForeignKey('trading_calendars.日期'),
                  name='日期')
    m1 = Column(Float)
    m3 = Column(Float)
    m6 = Column(Float)
    y1 = Column(Float)
    y2 = Column(Float)
    y3 = Column(Float)
    y5 = Column(Float)
    y7 = Column(Float)
    y10 = Column(Float)
    y20 = Column(Float)
    y30 = Column(Float)


class Margin(Base):
    """融资融券"""
    code = Column(String(6),
                  ForeignKey('stocks.股票代码'),
                  index=True,
                  name='股票代码')
    date = Column(Date,
                  ForeignKey('trading_calendars.日期'),
                  index=True,
                  name='日期')
    A001_融资余额 = Column(Float, name='融资余额')
    A002_融资买入额 = Column(Float, name='融资买入额')
    A003_融资偿还额 = Column(Float, name='融资偿还额')
    A004_融券余量 = Column(Float, name='融券余量')
    A005_融券卖出量 = Column(Float, name='融券卖出量')
    A006_融券偿还量 = Column(Float, name='融券偿还量')
    A007_融券余量金额 = Column(Float, name='融券余量金额')
    A008_融券余额 = Column(Float, name='融券余额')

    stock = relationship("Stock", back_populates="margins")


Stock.margins = relationship("Margin",
                             order_by=Margin.date,
                             back_populates="stock")


class Adjustment(Base):
    """分红派息"""
    code = Column(String(6),
                  ForeignKey('stocks.股票代码'),
                  index=True,
                  name='股票代码')
    date = Column(Date,
                  ForeignKey('trading_calendars.日期'),
                  index=True,
                  name='日期')  # 实施日期
    A001_分红年度 = Column(String, name='分红年度')
    A002_派息 = Column(Float, name='派息')
    A003_送股 = Column(Float, name='送股')
    A004_股权登记日 = Column(Date, name='股权登记日')
    A005_除权基准日 = Column(Date, name='除权基准日')
    A006_红股上市日 = Column(Date, name='红股上市日')

    stock = relationship("Stock", back_populates="adjustments")


Stock.adjustments = relationship("Adjustment",
                                 order_by=Adjustment.date,
                                 back_populates="stock")


class DealDetail(Base):
    """成交明细"""
    code = Column(String(6),
                  ForeignKey('stocks.股票代码'),
                  index=True,
                  name='股票代码')
    date = Column(Date,
                  ForeignKey('trading_calendars.日期'),
                  index=True,
                  name='日期')
    A001_时间 = Column(String(8), name='时间')
    A002_价格 = Column(Float, name='价格')
    A003_涨跌额 = Column(Float, name='涨跌额')
    A004_成交量 = Column(Integer, name='成交量')
    A005_成交额 = Column(Float, name='成交额')
    A006_方向 = Column(String, name='方向')

    stock = relationship("Stock", back_populates="deal_details")


Stock.deal_details = relationship("DealDetail",
                                  order_by=DealDetail.date,
                                  back_populates="stock")


class Quotation(Base):
    """股票报价（五档）"""
    code = Column(String(6),
                  ForeignKey('stocks.股票代码'),
                  index=True,
                  name='股票代码')
    date = Column(Date,
                  ForeignKey('trading_calendars.日期'),
                  index=True,
                  name='日期')
    A001_时间 = Column(String(8), name='时间')
    A002_股票简称 = Column(String, name='股票简称')
    A003_开盘 = Column(Float, name='开盘')
    A004_前收盘 = Column(Float, name='前收盘')
    A005_现价 = Column(Float, name='现价')
    A006_最高 = Column(Float, name='最高')
    A007_最低 = Column(Float, name='最低')
    A008_竞买价 = Column(Float, name='竞买价')
    A009_竞卖价 = Column(Float, name='竞卖价')
    A010_成交量 = Column(Integer, name='成交量')  # 累计
    A011_成交额 = Column(Float,  name='成交额')   # 累计
    A012_买1量 = Column(Integer, name='买1量')
    A013_买1价 = Column(Float,   name='买1价')
    A014_买2量 = Column(Integer, name='买2量')
    A015_买2价 = Column(Float,   name='买2价')
    A016_买3量 = Column(Integer, name='买3量')
    A017_买3价 = Column(Float,   name='买3价')
    A018_买4量 = Column(Integer, name='买4量')
    A019_买4价 = Column(Float,   name='买4价')
    A020_买5量 = Column(Integer, name='买5量')
    A021_买5价 = Column(Float,   name='买5价')
    A022_卖1量 = Column(Integer, name='卖1量')
    A023_卖1价 = Column(Float,   name='卖1价')
    A024_卖2量 = Column(Integer, name='卖2量')
    A025_卖2价 = Column(Float,   name='卖2价')
    A026_卖3量 = Column(Integer, name='卖3量')
    A027_卖3价 = Column(Float,   name='卖3价')
    A028_卖4量 = Column(Integer, name='卖4量')
    A029_卖4价 = Column(Float,   name='卖4价')
    A030_卖5量 = Column(Integer, name='卖5量')
    A031_卖5价 = Column(Float,   name='卖5价')

    stock = relationship("Stock", back_populates="quotations")


Stock.quotations = relationship("Quotation",
                                order_by=Quotation.date,
                                back_populates="stock")


class RefreshRecord(Base):
    """刷新记录"""
    table_name = Column(String, name='表名')
    status = Column(Boolean, name='状态')
    row = Column(Integer, name='行数')
    action = Column(Enum(Action), name='操作')
    code = Column(String, name='代码')
    start = Column(Date, name='开始日期')
    end = Column(Date, name='结束日期')