import { ref } from 'vue'

const currentCity = ref('兰州市')

const cities = [
  '兰州市', '嘉峪关市', '金昌市', '白银市', '天水市',
  '武威市', '张掖市', '平凉市', '酒泉市', '庆阳市',
  '定西市', '陇南市', '临夏州', '甘南州'
]

export function useCity() {
  return { currentCity, cities }
}
