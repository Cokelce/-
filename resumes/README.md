# 简历目录

请将您的简历图片文件放在此目录中。

## 支持的格式

- JPG/JPEG
- PNG

## 命名建议

为不同平台准备不同的简历图片，并使用以下命名规则：

- `resume_boss.jpg` - Boss直聘图片简历
- `resume_zhilian.jpg` - 智联招聘图片简历
- `resume_qiancheng.jpg` - 前程无忧图片简历
- `resume_lagou.jpg` - 拉勾网图片简历

## 图片建议

1. 简历图片应清晰可读，分辨率建议在 1200x1600 左右
2. 文件大小建议控制在 1MB 以内
3. 内容应包含您的个人信息、教育背景、工作经历、技能特长等
4. 设计应简洁专业，避免过度设计和不必要的图形元素

## 使用说明

在`config.py`文件中，可以配置每个平台使用的简历图片路径，如：

```python
"resume_path": "resumes/resume_boss.jpg"  # Boss直聘图片简历路径
``` 