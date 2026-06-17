# Atmosphere_Kit — 大气层整合包生成脚本

## 功能如下：

- 下载最新：
  - 大气层核心
    - [x] `Atmosphere + Fusee` [From Here](https://github.com/Atmosphere-NX/Atmosphere/releases/latest)
    - [x] `Hekate + Nyx` 官方版 [From Here](https://github.com/CTCaer/hekate/releases/latest)
  - Payload 插件
    - [x] 主机系统的密钥提取工具 `Lockpick_RCM` [From Here](https://github.com/Kofysh/Lockpick_RCM/releases/latest)
    - [x] Hekate 下的文件管理工具 `TegraExplorer` [From Here](https://github.com/suchmememanyskill/TegraExplorer/releases/latest)
  - Nro 插件
    - [x] 联网检测是否屏蔽任天堂服务器 `Switch_90DNS_tester` [From Here](https://github.com/meganukebmp/Switch_90DNS_tester/releases/latest)
    - [x] 游戏安装、存档管理和文件传输工具 `DBI`（中文汉化版） [From Here](https://github.com/rashevskyv/DBIPatcher/releases/latest)
    - [x] 系统升级工具 `daybreak` （随 Atmosphere 官方包内置）
  - Ultrahand Overlay 框架
    - [x] 加载器 `nx-ovlloader` [From Here](https://github.com/WerWolv/nx-ovlloader/releases/latest)
    - [x] 菜单 `Ultrahand-Overlay` [From Here](https://github.com/ppkantorski/Ultrahand-Overlay/releases/latest)
  - Ovl 插件
    - [x] 金手指工具 `EdiZon` [From Here](https://github.com/proferabg/EdiZon-Overlay/releases/latest)
    - [x] 系统模块管理 `ovl-sysmodules` [From Here](https://github.com/ppkantorski/ovl-sysmodules/releases/latest)
    - [x] 系统监视 `StatusMonitor` [From Here](https://github.com/masagrator/Status-Monitor-Overlay/releases/latest)
    - [x] 掌机底座模式切换 `ReverseNX-RT` [From Here](https://github.com/masagrator/ReverseNX-RT/releases/latest)
    - [x] 局域网联机 `ldn_mitm` [From Here](https://github.com/spacemeowx2/ldn_mitm/releases/latest)
    - [x] 虚拟 Amiibo `emuiibo` [From Here](https://github.com/XorTroll/emuiibo/releases/latest)
    - [x] 时间同步 `QuickNTP` [From Here](https://github.com/nedex/QuickNTP/releases/latest)
    - [x] 系统签名补丁 `sys-patch` [From Here](https://github.com/impeeza/sys-patch/releases/latest)
    - [x] 超频插件 `sys-clk` [From Here](https://github.com/retronx-team/sys-clk/releases/latest)
  - 其他
    - [x] 蓝牙手柄插件 `MissionControl` [From Here](https://github.com/ndeadly/MissionControl/releases/latest)

- 文件操作：
    - [x] 移动 `fusee.bin` 至 `bootloader/payloads` 文件夹
    - [x] 将 `hekate_ctcaer_*.bin` 重命名为 `payload.bin`
    - [x] 在 `bootloader` 文件夹中创建 `hekate_ipl.ini`
    - [x] 在根目录中创建 `exosphere.ini`
    - [x] 在 `atmosphere/hosts` 文件夹中创建 `emummc.txt` 和 `sysmmc.txt`
    - [x] 在根目录中创建 `boot.ini`
    - [x] 在 `atmosphere/config` 文件夹中创建 `override_config.ini`
    - [x] 在 `atmosphere/config` 文件夹中创建 `system_settings.ini`
    - [x] 删除 `switch` 文件夹中 `haze.nro`
    - [x] 删除 `switch` 文件夹中 `reboot_to_payload.nro`

## 插件使用说明

### Ultrahand Overlay（系统模块 & overlay 管理菜单）

- **唤醒键：ZL + ZR + 方向键下**（须在游戏或 Homebrew 内按下，主菜单无效）
- 与 Tesla Menu 共用底层加载器 nx-ovlloader，但唤醒键不同（Tesla 是 L+R+方向键下）；本整合包使用 Ultrahand 替代 Tesla Menu
- 内置系统模块开关（等同 ovl-sysmodules）、文件操作、自定义脚本（package.ini）
- 通过菜单内 **ovl-sysmodules** 启用 / 禁用 ldn_mitm、sys-clk 等各 sysmodule

---

## 使用说明

  - 安装 `jq` 工具
  - 运行脚本（switchScript.sh）

## 关于任天堂域名屏蔽

CFW 模式下 Atmosphere 通过 `atmosphere/hosts/` 把任天堂域名全部黑洞到 `127.0.0.1`，避免遥测/上报。所以 Switch 连接测试会显示失败。

## GitHub Actions 所需 Secrets
| Secret | 说明 |
|--------|------|
| `TOKEN` | 具有 `repo` 权限的 GitHub Personal Access Token（PAT），用于创建 Release 和清理旧 Workflow Run |

## 致谢

本项目基于以下上游项目的思路和代码发展而来，感谢原作者们的贡献：

| 项目 | 地址 |
|------|------|
| huangqian8/SwitchScript（主要上游） | https://github.com/huangqian8/SwitchScript |
| 上游授权 | https://github.com/huangqian8/SwitchScript/issues/33 |
| Fraxalotl（原始脚本作者） | https://rentry.org/CFWGuides |


## 参考资料

| 资料 | 地址 |
|------|------|
| Switchbrew Title List（Switch 官方及 Homebrew Title ID 总表） | https://switchbrew.org/wiki/Title_list |
