/**
 * 港口代码 <-> 名称 映射工具
 */

// PORT代码 -> 中文名 映射
export const PORT_NAME_MAP = {
  'PORT01': '默认港口',
  'PORT02': '上海',
  'PORT03': '深圳',
  'PORT04': '广州',
  'PORT05': '宁波',
  'PORT06': '青岛',
  'PORT07': '天津',
  'PORT08': '大连',
  'PORT09': '厦门',
  'PORT10': '香港',
  'PORT11': '釜山'
}

// 中文名 -> PORT代码 映射（反向）
export const NAME_PORT_MAP = Object.fromEntries(
  Object.entries(PORT_NAME_MAP).map(([code, name]) => [name, code])
)

/**
 * 将港口代码转换为中文名
 * @param {string} code - 港口代码，如 'PORT02'
 * @returns {string} 中文名，如 '上海'；如果不是代码则原样返回
 */
export function getPortName(code) {
  if (!code) return code
  return PORT_NAME_MAP[code] || code
}

/**
 * 将中文名转换为港口代码
 * @param {string} name - 中文名，如 '上海'
 * @returns {string} 港口代码，如 'PORT02'；如果不是名称则原样返回
 */
export function getPortCode(name) {
  if (!name) return name
  return NAME_PORT_MAP[name] || name
}

/**
 * 将路径数组中的港口代码转换为中文名
 * @param {string[]} path - 路径数组，如 ['PORT02', 'PORT08']
 * @returns {string[]} 中文名数组，如 ['上海', '大连']
 */
export function convertPathToNames(path) {
  if (!Array.isArray(path)) return path
  return path.map(getPortName)
}

/**
 * 将订单信息中的港口代码转换为中文名（用于显示）
 * @param {object} order - 订单对象
 * @returns {object} 转换后的订单对象（新对象，不修改原对象）
 */
export function convertOrderPorts(order) {
  if (!order) return order
  return {
    ...order,
    orig_port: getPortName(order.orig_port),
    dest_port: getPortName(order.dest_port)
  }
}
