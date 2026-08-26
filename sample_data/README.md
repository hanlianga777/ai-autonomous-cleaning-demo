# Camera Event Demo Assets

Phase 8 的客户工作台不会生成或伪造“真实现场照片”。请按以下路径提供 Scenario 02 的经授权实拍素材；文件名必须保持不变。

```text
camera_events/
├── CAM-A1-01/event-beverage-spill-002/
│   ├── primary.jpg       # 奶茶/液体重污主视角（清洁前）
│   ├── after.jpg         # 同一固定摄像头的清洁后画面
│   └── metadata.json
├── CAM-A1-02/event-beverage-spill-002/
│   ├── secondary.jpg     # 同一事件的补充视角
│   └── metadata.json
└── CAM-A1-03/event-beverage-spill-002/
    ├── secondary.jpg     # 同一事件的补充视角
    └── metadata.json
```

建议图片为 16:9、至少 1280×720，避免拍入人脸、车牌或其他敏感信息。素材只描述摄像头、事件和视角关系；AI 判断仍复用 `ai-lab.v1` / Phase 4 perception schema。
