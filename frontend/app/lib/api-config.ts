/** ブラウザから API を叩くベース URL（`VITE_API_BASE_URL` 未設定時は相対パスになり Vite に当たるためフォールバック） */
export const CLIENT_API_BASE =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8001'
