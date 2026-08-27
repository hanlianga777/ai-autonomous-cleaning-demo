# Camera Event Demo Assets

本目录保存用户授权、仅用于本地 PoC / GitHub Demo 的四组固定摄像头素材。工作台不会生成或篡改“真实现场照片”。

```text
camera_events/
├── CAM-OUT-01/event-outdoor-tissue-001/
│   ├── primary.png / after.png       # 室外纸巾：Robot A
├── CAM-A1-01/event-beverage-spill-002/
│   ├── primary.png / after.png       # 奶茶污渍主视角：Robot B
├── CAM-A1-02/event-beverage-spill-002/secondary.png
├── CAM-A1-04/event-beverage-spill-002/secondary.png
│                                      # 两个补充视角：Phase 5 Multi-view
├── CAM-A2-08/event-indoor-can-003/
│   ├── primary.png / after.png       # 二楼易拉罐：Robot C
└── CAM-A2-11/event-oversized-box-004/
    └── primary.png                   # 大型纸箱：Human Fallback，无 after 图
```

每个事件目录的 `metadata.json` 仅描述 Camera、Event、View 与预期业务边界。`/api/workbench/upload` 对上传内容计算 SHA-256，只接受这四张受控的清洁前原图进行自动场景匹配；未知上传会返回明确错误，绝不默认成某个清洁事件。

其中 Scenario 04 没有清洁后图是刻意保留的业务事实：大型纸箱必须创建人工工单，工作台只能显示“等待人工回传验收”，不能伪造自动验收通过。
