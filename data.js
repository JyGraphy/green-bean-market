const FLAG = {
  '에티오피아':'🇪🇹','케냐':'🇰🇪','탄자니아':'🇹🇿','르완다':'🇷🇼','세인트헬레나':'🌍',
  '브라질':'🇧🇷','콜롬비아':'🇨🇴','과테말라':'🇬🇹','코스타리카':'🇨🇷','파나마':'🇵🇦',
  '엘살바도르':'🇸🇻','온두라스':'🇭🇳','멕시코':'🇲🇽','자메이카':'🇯🇲','페루':'🇵🇪',
  '인도네시아':'🇮🇩','인도':'🇮🇳','베트남':'🇻🇳','하와이':'🌺',
  '볼리비아':'🇧🇴','에콰도르':'🇪🇨','예멘':'🇾🇪','중국':'🇨🇳',
  '파푸아뉴기니':'🇵🇬','니카라과':'🇳🇮','우간다':'🇺🇬','콩고민주공화국':'🇨🇩',
};

const STORE_CLS = {
  '커피플랜트':'sp-cp','커피창고':'sp-cg','엠아이커피':'sp-mi','모모스커피':'sp-momos','코빈즈커피':'sp-cobeans',
  '아얀투':'sp-ayantu','오로미아코리아':'sp-oromia','지에스씨(GSC)':'sp-gsc','오월의숲':'sp-mayforest',
  '커피리브레':'sp-cl','블레스빈':'sp-bb','콤파스커피':'sp-compass','팔콘커피':'sp-falcon',
  '더블유빈':'sp-wbean','커만사':'sp-comansa'
};

const PROC_CLS = {
  '워시드':'proc-washed','내추럴':'proc-natural','허니':'proc-honey',
  '무산소발효':'proc-anaerobic','펄프드내추럴':'proc-pulped','웻훌드':'proc-wethulled',
  '디카페인':'proc-decaf','알수없음':'proc-unknown'
};

const PROC_COLORS = {
  '워시드':'#1d4ed8','내추럴':'#92400e','허니':'#9d174d',
  '무산소발효':'#6b21a8','펄프드내추럴':'#9a3412','웻훌드':'#166534',
  '디카페인':'#0f766e','알수없음':'#9ca3af'
};

function extractProcess(name) {
  const n = (name||'').toLowerCase();
  if (/무산소|anaerobic|애너러빅|카보닉|carbonic|코퍼먼티드|co.?ferment|인퓨즈드/.test(n)) return '무산소발효';
  if (/펄프드.?내추럴|pulped.?natural/.test(n))   return '펄프드내추럴';
  if (/워시드|washed|fully.?washed/.test(n))       return '워시드';
  if (/세미워시드|semi.?washed|레드허니|옐로허니|화이트허니|블랙허니|황허니|ff오렌지|hf시나몬/.test(n)) return '허니';
  if (/허니|honey/.test(n))                         return '허니';
  if (/내추럴|natural|레포사도/.test(n))            return '내추럴';
  if (/웻.?훌|웻.?헐|wet.?hul|웻.?펄프/.test(n))  return '웻훌드';
  return '알수없음';
}
