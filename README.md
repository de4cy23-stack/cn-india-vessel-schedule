# CN-India Vessel Schedule Aggregator

面向货代日常工作的中印船期聚合查询器。

## MVP 目标

输入起运港、目的港和日期范围，一次查询多家船司，并统一返回：

- 船司
- 船名 / 航次
- ETD（预计开船）
- ETA（预计到港）
- Transit Time
- 直达 / 中转
- 中转港
- 数据更新时间

首批重点航线：

- Ningbo -> Nhava Sheva / JNPT
- Ningbo -> Mundra
- Shanghai -> Nhava Sheva / JNPT
- Shanghai -> Mundra

## 船司接入状态

| 船司 | SCAC / Carrier Code | 第一版状态 | 接入方式 |
|---|---|---|---|
| Maersk | MAEU | Enabled when credentials are configured | Official schedule API |
| CMA CGM | CMDU | Enabled when credentials are configured | Official Routing / DCSA schedule API |
| ONE | ONEY | Enabled when credentials are configured | Official Point-to-Point / Vessel Schedule API |
| HMM | HDMU | Enabled when credentials are configured | Official Schedule API |
| Hapag-Lloyd | HLCU | Enabled when credentials are configured | Official vessel schedule API |
| MSC | MSCU | Reserved | Official/public integration to be verified |
| COSCO | COSU | Reserved | Official/public integration to be verified |
| OOCL | OOLU | Reserved | Official/public integration to be verified |
| Evergreen | EGLV | Reserved | Official/public integration to be verified |

> 说明：不把尚未验证的网页接口伪装成稳定 API。先使用官方 API；无官方可用接口时，再单独增加浏览器自动化 / 网页适配器。

## 后端

FastAPI + httpx。所有船司最终归一化为统一 Schedule 数据结构。

### 运行

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate

pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

打开：

- API docs: http://127.0.0.1:8000/docs
- Carriers: http://127.0.0.1:8000/carriers

### 示例

```
GET /schedules?origin=CNNGB&destination=INNSA&date_from=2026-09-20&weeks=4
```

## 安全

API Key / OAuth secret 不写进 GitHub。全部放在本地 `.env` 或部署平台 Secret 中。
