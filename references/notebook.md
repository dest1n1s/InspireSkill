# Notebook 工作流

## 什么时候加载

当任务需要创建 notebook、SSH 连接、远程执行、传文件、保存镜像、安装 Slurm/Ray 依赖，或判断 `shell` 与 `exec` 的差异时，加载本文档。

## 1. 常用命令

| 命令 | 用途 |
| --- | --- |
| `inspire notebook list -A -s RUNNING --name <keyword>` | 列实例 |
| `inspire notebook create --workspace X --group Y -q <gpu,cpu,mem> --name <name> --image URL --project P --wait` | 创建实例并等待 RUNNING |
| `inspire notebook status <name>` | 详情，镜像名在人类输出里可见 |
| `inspire notebook events <name> --tail 50` | 生命周期事件 |
| `inspire notebook lifecycle <name>` | 多次启停的粗粒度时间线 |
| `inspire notebook ssh <name>` | Bootstrap SSH |
| `inspire notebook exec <name> "<cmd>"` | 一次性远程命令 |
| `inspire notebook shell <name>` | 持久交互 SSH |
| `inspire notebook scp <name> <src> <dst>` | 传非仓库文件 |
| `inspire notebook test <name>` | 连通性测试 |
| `inspire notebook refresh <name>` | notebook 重启后刷新 SSH 缓存 |
| `inspire notebook connections` | 列已 bootstrap 的 notebook |
| `inspire notebook forget <name>` | 清本地 SSH 缓存 |
| `inspire notebook top --watch` | 实时 `nvidia-smi` |

## 2. `shell` 与 `exec`

`inspire notebook shell <name>` 是持久 SSH 会话，cwd、环境变量和 history 会保留到 `exit`。多个终端并开就是多个独立会话，互相共享同一容器资源。

`inspire notebook exec <name> "<cmd>"` 是一次性独立子进程。两次调用之间不共享 cwd 或环境变量。需要连续状态时，把状态放在同一条命令里：

```bash
inspire notebook exec <name> "cd <repo> && export X=1 && ./run.sh"
```

超过 $$20$$ 分钟的任务写成远端后台进程和 sentinel 文件，再从本机轮询，不要让 `exec` 同步等待。

## 3. SSH bootstrap

`inspire notebook ssh <name>` 对任何镜像、计算组和公网状态都应可用。CLI 会在容器里启动 sshd 和 rtunnel，通路缓存到本地。失败时加载 [troubleshooting.md](troubleshooting.md)。

冷启动时间很贵时，可以 `image save` 派生镜像固化环境；一次性任务用完即弃即可。

## 4. 代码与文件流转

| 场景 | 做法 |
| --- | --- |
| 独立 repo 日常同步 | 本地 `git push`，远端 `git pull` |
| 多仓库工作区 | 通过 `inspire init --discover` 配好项目远端工作目录，多个 repo 并列放置 |
| 非 Git 文件 | `notebook scp`，远端路径优先写绝对路径 |
| 目标计算组不可上网但共享路径可见 | 在同一路径的可上网区 notebook 做 git 操作，离线训练实例只读共享盘结果 |

日常闭环：

```bash
git push origin <branch>
inspire notebook exec <notebook-name> "cd <repo> && git pull && git log -1 --oneline"
inspire notebook ssh <notebook-name>
inspire notebook exec <notebook-name> "hostname"
```

## 5. 基底 notebook 与镜像

项目刚开始时，建议在可上网 CPU 空间用 `docker.sii.shaipower.online/inspire-studio/unified-base:v2` 起一个基底 notebook，把 Slurm、Ray、分布式训练依赖和项目依赖一次性装好，再保存成项目通用镜像。

```bash
inspire notebook create --workspace CPU资源空间 --group CPU资源-2 -q 0,20,256 \
  --name cpu-box --image docker.sii.shaipower.online/inspire-studio/unified-base:v2 \
  --project <P> --wait

inspire notebook ssh cpu-box
inspire notebook exec cpu-box "apt-get update && apt-get install -y <deps> && pip install <pkgs>"
inspire image save cpu-box -n <img> -v v1 --public --wait
inspire image set-default --job <URL> --notebook <URL>
```

已有 Ubuntu 镜像需要补 Slurm/Ray 依赖时：

```bash
inspire notebook install-deps <name> --slurm --ray
```

该命令会先 probe 再安装，已存在的组件会跳过。普通 notebook 中 Slurm 命令因无 controller 报错是平台设计，只有 `hpc create` 路径下才注入 controller。
