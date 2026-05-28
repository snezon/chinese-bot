"""
Approximate Russian phonetic transcription for pinyin syllables.
Used in lesson theory to help beginners pronounce Chinese words.
"""
import re

_TABLE = {
    # zh- series
    'zhi':'чжи','zha':'чжа','zhai':'чжай','zhan':'чжань','zhang':'чжан',
    'zhao':'чжао','zhe':'чжэ','zhei':'чжэй','zhen':'чжэнь','zheng':'чжэн',
    'zhong':'чжун','zhou':'чжоу','zhu':'чжу','zhua':'чжуа','zhuai':'чжуай',
    'zhuan':'чжуань','zhuang':'чжуан','zhui':'чжуэй','zhun':'чжунь','zhuo':'чжо',
    # ch- series
    'chi':'чи','cha':'ча','chai':'чай','chan':'чань','chang':'чан',
    'chao':'чао','che':'чэ','chen':'чэнь','cheng':'чэн',
    'chong':'чун','chou':'чоу','chu':'чу','chuai':'чуай',
    'chuan':'чуань','chuang':'чуан','chui':'чуэй','chun':'чунь','chuo':'чо',
    # sh- series
    'shi':'ши','sha':'ша','shai':'шай','shan':'шань','shang':'шан',
    'shao':'шао','she':'шэ','shei':'шэй','shen':'шэнь','sheng':'шэн',
    'shou':'шоу','shu':'шу','shua':'шуа','shuai':'шуай',
    'shuan':'шуань','shuang':'шуан','shui':'шуэй','shun':'шунь','shuo':'шо',
    # r- series
    'ri':'жи','ran':'жань','rang':'жан','rao':'жао','re':'жэ',
    'ren':'жэнь','reng':'жэн','rong':'жун','rou':'жоу',
    'ru':'жу','ruan':'жуань','rui':'жуэй','run':'жунь','ruo':'жо',
    # z- series
    'zi':'цзы','za':'цза','zai':'цзай','zan':'цзань','zang':'цзан',
    'zao':'цзао','ze':'цзэ','zei':'цзэй','zen':'цзэнь','zeng':'цзэн',
    'zong':'цзун','zou':'цзоу','zu':'цзу','zuan':'цзуань',
    'zui':'цзуэй','zun':'цзунь','zuo':'цзо',
    # c- series
    'ci':'цзы','ca':'цза','cai':'цзай','can':'цзань','cang':'цзан',
    'cao':'цзао','ce':'цзэ','cen':'цзэнь','ceng':'цзэн',
    'cong':'цзун','cou':'цзоу','cu':'цзу','cuan':'цзуань',
    'cui':'цзуэй','cun':'цзунь','cuo':'цзо',
    # s- series
    'si':'сы','sa':'са','sai':'сай','san':'сань','sang':'сан',
    'sao':'сао','se':'сэ','sen':'сэнь','seng':'сэн',
    'song':'сун','sou':'соу','su':'су','suan':'суань',
    'sui':'суэй','sun':'сунь','suo':'со',
    # j- series (j+i/ü)
    'ji':'цзи','jia':'цзя','jian':'цзянь','jiang':'цзян',
    'jiao':'цзяо','jie':'цзе','jin':'цзинь','jing':'цзин',
    'jiong':'цзюн','jiu':'цзю','ju':'цзюй',
    'juan':'цзюань','jue':'цзюэ','jun':'цзюнь',
    # q- series
    'qi':'чи','qia':'чя','qian':'чянь','qiang':'чян',
    'qiao':'чяо','qie':'чье','qin':'чинь','qing':'чин',
    'qiong':'чюн','qiu':'чю','qu':'чюй',
    'quan':'чюань','que':'чюэ','qun':'чюнь',
    # x- series
    'xi':'си','xia':'ся','xian':'сянь','xiang':'сян',
    'xiao':'сяо','xie':'се','xin':'синь','xing':'син',
    'xiong':'сюн','xiu':'сю','xu':'сюй',
    'xuan':'сюань','xue':'сюэ','xun':'сюнь',
    # b- series
    'ba':'ба','bai':'бай','ban':'бань','bang':'бан',
    'bao':'бао','bei':'бэй','ben':'бэнь','beng':'бэн',
    'bi':'би','bian':'бянь','biao':'бяо','bie':'бье',
    'bin':'бинь','bing':'бин','bo':'бо','bu':'бу',
    # p- series
    'pa':'па','pai':'пай','pan':'пань','pang':'пан',
    'pao':'пао','pei':'пэй','pen':'пэнь','peng':'пэн',
    'pi':'пи','pian':'пянь','piao':'пяо','pie':'пье',
    'pin':'пинь','ping':'пин','po':'по','pou':'поу','pu':'пу',
    # m- series
    'ma':'ма','mai':'май','man':'мань','mang':'ман',
    'mao':'мао','mei':'мэй','men':'мэнь','meng':'мэн',
    'mi':'ми','mian':'мянь','miao':'мяо','mie':'мье',
    'min':'минь','ming':'мин','miu':'мю','mo':'мо','mou':'моу','mu':'му',
    # f- series
    'fa':'фа','fan':'фань','fang':'фан','fei':'фэй',
    'fen':'фэнь','feng':'фэн','fo':'фо','fou':'фоу','fu':'фу',
    # d- series
    'da':'да','dai':'дай','dan':'дань','dang':'дан',
    'dao':'дао','de':'дэ','dei':'дэй','deng':'дэн',
    'di':'ди','dian':'дянь','diao':'дяо','die':'дье',
    'ding':'дин','diu':'дю','dong':'дун','dou':'доу',
    'du':'ду','duan':'дуань','dui':'дуэй','dun':'дунь','duo':'до',
    # t- series
    'ta':'та','tai':'тай','tan':'тань','tang':'тан',
    'tao':'тао','te':'тэ','teng':'тэн',
    'ti':'ти','tian':'тянь','tiao':'тяо','tie':'тье',
    'ting':'тин','tong':'тун','tou':'тоу',
    'tu':'ту','tuan':'туань','tui':'туэй','tun':'тунь','tuo':'то',
    # n- series
    'na':'на','nai':'най','nan':'нань','nang':'нан',
    'nao':'нао','ne':'нэ','nei':'нэй','nen':'нэнь','neng':'нэн',
    'ni':'ни','nian':'нянь','niang':'нян','niao':'няо','nie':'нье',
    'nin':'нинь','ning':'нин','niu':'ню','nong':'нун','nou':'ноу',
    'nu':'ну','nuan':'нуань','nuo':'но','nü':'нюй','nüe':'нюэ',
    # l- series
    'la':'ла','lai':'лай','lan':'лань','lang':'лан',
    'lao':'лао','le':'лэ','lei':'лэй','leng':'лэн',
    'li':'ли','lia':'ля','lian':'лянь','liang':'лян',
    'liao':'ляо','lie':'лье','lin':'линь','ling':'лин',
    'liu':'лю','long':'лун','lou':'лоу',
    'lu':'лу','luan':'луань','lun':'лунь','luo':'ло',
    'lü':'люй','lüe':'люэ',
    # g- series
    'ga':'га','gai':'гай','gan':'гань','gang':'ган',
    'gao':'гао','ge':'гэ','gei':'гэй','gen':'гэнь','geng':'гэн',
    'gong':'гун','gou':'гоу','gu':'гу','gua':'гуа',
    'guai':'гуай','guan':'гуань','guang':'гуан','gui':'гуэй',
    'gun':'гунь','guo':'го',
    # k- series
    'ka':'ка','kai':'кай','kan':'кань','kang':'кан',
    'kao':'као','ke':'кэ','ken':'кэнь','keng':'кэн',
    'kong':'кун','kou':'коу','ku':'ку','kua':'куа',
    'kuai':'куай','kuan':'куань','kuang':'куан','kui':'куэй',
    'kun':'кунь','kuo':'ко',
    # h- series
    'ha':'ха','hai':'хай','han':'хань','hang':'хан',
    'hao':'хао','he':'хэ','hei':'хэй','hen':'хэнь','heng':'хэн',
    'hong':'хун','hou':'хоу','hu':'ху','hua':'хуа',
    'huai':'хуай','huan':'хуань','huang':'хуан','hui':'хуэй',
    'hun':'хунь','huo':'хо',
    # y- standalone
    'ya':'я','yan':'янь','yang':'ян','yao':'яо',
    'ye':'е','yi':'и','yin':'инь','ying':'ин',
    'yong':'юн','you':'ю','yu':'юй',
    'yuan':'юань','yue':'юэ','yun':'юнь',
    # w- standalone
    'wa':'уа','wai':'уай','wan':'уань','wang':'уан',
    'wei':'вэй','wen':'вэнь','weng':'вэн','wo':'во','wu':'у',
    # finals standalone
    'er':'эр','a':'а','ai':'ай','an':'ань','ang':'ан','ao':'ао',
    'e':'э','ei':'эй','en':'энь','eng':'эн','o':'о','ou':'оу',
}

_TONE_MAP = str.maketrans(
    'āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ',
    'aaaaeeeeiiiioooouuuuüüüü'
)


def pinyin_to_ru(pinyin: str) -> str:
    """Convert pinyin string (single or multi-syllable) to Russian approximation."""
    s = pinyin.lower().translate(_TONE_MAP)
    s = re.sub(r'[1-5\s]+', ' ', s).strip()
    parts = []
    for syl in s.split():
        parts.append(_TABLE.get(syl, syl))
    return '-'.join(parts)
