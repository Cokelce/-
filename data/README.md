# 数据目录

此目录用于存储程序运行过程中产生的数据文件。

## 主要文件说明

- `applications.json` - 职位投递记录
- `blacklist.json` - 公司黑名单
- `boss/profile.json` - Boss直聘用户简历缓存

## 数据结构说明

### applications.json

职位投递记录，包含以下字段：

```json
[
  {
    "platform": "boss",
    "job_id": "123456",
    "job_title": "Python开发工程师",
    "company": "某公司",
    "status": "已投递",
    "applied_at": "2023-01-01 12:34:56"
  }
]
```

### blacklist.json

公司黑名单，包含以下字段：

```json
[
  {
    "company": "某问题公司",
    "reasons": ["HR不活跃", "面试体验差"],
    "created_at": "2023-01-01 12:34:56",
    "updated_at": "2023-01-02 12:34:56"
  }
]
```

### boss/profile.json

Boss直聘用户简历缓存，根据Boss直聘API返回的用户简历信息存储。

## 注意事项

- 请勿手动删除或修改这些文件，以免影响程序正常运行
- 如需重置数据，可以备份后删除相应文件，程序将自动创建新的数据文件 