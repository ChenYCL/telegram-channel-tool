# Telegram Channel Search and Management Tool

这是一个功能强大的Python脚本，用于搜索Telegram频道、查找相似频道，并管理您的Telegram账户。

## 功能

1. 根据关键词搜索Telegram频道
2. 搜索频道并获取相似频道
3. 为特定频道查找相似频道
4. 清理已删除账户的对话
5. 结果缓存和自动保存

## 安装

1. 克隆此仓库：
   ```
   git clone https://github.com/ChenYCL/telegram-channel-tool.git
   cd telegram-channel-tool
   ```

2. 安装所需的Python包：
   ```
   pip install -r requirements.txt
   ```

3. 创建一个 `.env` 文件，并添加以下内容：
   ```
   TELEGRAM_API_ID=你的API_ID
   TELEGRAM_API_HASH=你的API_HASH
   TELEGRAM_PHONE_NUMBER=你的电话号码
   ```
   请确保将上述占位符替换为您的实际Telegram API凭据和电话号码。

## 使用说明

1. 运行脚本：
   ```
   python main.py
   ```

2. 首次运行时，您可能需要输入Telegram发送的验证码。如果您启用了两步验证，还需要输入您的2FA密码。

3. 主菜单将显示可用的功能选项：
   - 选项1：按关键词搜索频道
   - 选项2：搜索频道并获取相似频道
   - 选项3：为特定频道获取相似频道
   - 选项4：清理已删除账户的对话
   - 选项5：退出程序

4. 按照屏幕上的提示进行操作。

5. 搜索结果将自动保存在 `results` 文件夹中，按日期和查询类型分类。

## 注意事项

- 请谨慎使用此工具，避免过度频繁的请求，以免被Telegram限制。
- 清理已删除账户的对话是不可逆操作，请在执行前仔细确认。
- 所有操作都有确认步骤，以防止意外执行。

## 贡献

欢迎提交问题报告和改进建议！如果您想贡献代码，请先开启一个issue讨论您的想法。

## 许可证

[MIT License](LICENSE)