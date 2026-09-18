# CN-India Vessel Schedule Aggregator

面向货代日常工作的中印船期聚合查询器。核心目标很简单：**一次输入起运港、目的港和日期范围，汇总主要船司的 ETD / ETA。**

## 当前能力

- 多船司并发查询
- 统一船期模型：船司、船名、航次、ETD、ETA、航程、直达/中转、中转港
- DCSA Commercial Schedules Point-to-Point 结构解析
- API Key / Bearer Token / OAuth2 Client Credentials
- 429 / 5xx 基础重试
- 单家船司失败不会阻断其他船司结果
- 中文/英文港口别名
- 自动测试

常用港口可以直接输入：

- `宁波` / `Ningbo` / `CNNGB`
- `上海` / `Shanghai` / `CNSHA`
- `JNPT` / `Nhava Sheva` / `INNSA`
- `Mundra` / `INMUN`
- Chennai、Pipavav、Hazira、Kolkata

## 当前船司

| 船司 | Code | 状态 | 数据方式 |
|---|---|---|---|
| Maersk | MAEU | Adapter 已实现 | 官方 Ocean Commercial Schedules |
| CMA CGM | CMDU | Adapter 已实现 | 官方 DCSA Commercial Schedules |
| ONE | ONEY | Adapter 已实现 | 官方 DCSA Point-to-Point Schedule |
| HMM | HDMU | Adapter 已实现 | 官方 Port-to-Port Schedule |
| Hapag-Lloyd | HLCU | Adapter 已实现 | 官方 Commercial Schedule API |
| MSC | MSCU | Adapter 已实现 | 官方 DCSA Commercial Schedules Point-to-Point |
| COSCO | COSU | 预留 | 待验证稳定官方接口 |
| OOCL | OOLU | 预留 | 待验证稳定官方接口 |
| Evergreen | EGLV | Adapter 已实现 | 官方 DCSA Commercial Schedules |
| ZIM | ZIMU | Adapter 已实现 | 官方 DCSA Commercial Schedules Point-to-Point |
| Yang Ming | YMLU | Adapter 已实现 | 官方 DCSA Commercial Schedules Point-to-Point |

**Adapter 已实现不等于无需凭证即可实时查询。** 各船司的 Developer/API Portal 仍可能要求订阅、API Key 或 OAuth2 凭证。

详细数据源说明见 `docs/carrier-api-sources.md`。

## 运行

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
copy .env.example .env

uvicorn app.main:app --reload
```

打开：

- Web 查询页: http://127.0.0.1:8000/
- Swagger: http://127.0.0.1:8000/docs
- 港口: http://127.0.0.1:8000/ports
- 船司: http://127.0.0.1:8000/carriers

## 查询

推荐使用 `/search`，因为它除了船期外还会返回每一家船司的查询状态。

```text
GET /search?origin=宁波&destination=JNPT&date_from=2026-09-20&weeks=4
```

也可以只取船期数组：

```text
GET /schedules?origin=上海&destination=Mundra&date_from=2026-09-20&weeks=4
```

返回结果统一为：

```json
{
  "carrier": "CMA CGM",
  "carrier_code": "CMDU",
  "origin": "CNNGB",
  "destination": "INNSA",
  "vessel": "EXAMPLE VESSEL",
  "voyage": "001W",
  "etd": "2026-09-22T10:00:00+08:00",
  "eta": "2026-10-11T15:00:00+05:30",
  "transit_days": 19,
  "direct": false,
  "transshipment_ports": ["SGSIN"]
}
```

## 配置船司

复制 `backend/.env.example` 为 `backend/.env`，只启用已经取得官方凭证的船司，例如：

```env
MAERSK_ENABLED=true
MAERSK_API_KEY=your_consumer_key
```

其他船司同理。真实 Key、Client Secret、Bearer Token **不要提交到 GitHub**。

## 测试

```bash
cd backend
pytest -q
```

GitHub Actions 也会在 backend 代码发生变化时运行测试。


## 实时 API 连通性诊断

配置好 `backend/.env` 后，可以一次检查所有船司：

```bash
cd backend
python -m scripts.live_check --origin CNNGB --destination INNSA --weeks 4
```

只检查 Maersk：

```bash
python -m scripts.live_check --carrier maersk --origin CNSHA --destination INMUN
```

诊断程序不会输出 API Key / Client Secret。详细申请方式见 `docs/get-api-access.md`。
