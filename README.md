# tvOS IPA

Decrypted Apple TV + Apple Arcade IPAs (with `NSApplicationRequiresArcade` removed), published as an installable source.

**Subscribe URL:** `https://thedavidweng.github.io/tvOS-ipa/apps.json`

## Upload to Release

To upload an IPA package to [Release](https://github.com/thedavidweng/tvOS-ipa/releases), please name it as per the example.

### Naming Requirements

- Start with the application name without any **spaces** and **punctuation**. For example, for **Air Twister**, please name it `AirTwister`.
- Then the application version number, separated by **underscores**. For example, `AirTwister_1.4.0`.
- For injected plugins, please write the plugin name and version number, separated by **underscores**. For example, for **微信助手**, please name it `MiYou_1.1.1`.
- If you do not know the name and version number of the injected plugin, but only know that it is a cracked version, please write `Pro`. If it is just decrypted, append nothing.
- The application name, version, and plugin info are all connected by **underscores**. No trailing tag of any kind is added in this repo.

### Some Examples

`Air Twister (decrypted): AirTwister_1.4.0.ipa`

## 上传到 Release

将 IPA 软件包上传到 [Release](https://github.com/thedavidweng/tvOS-ipa/releases) 即可，请按照示例命名。

### 命名要求

- 以应用程序名称开头，不含任何 **空格** 和 **标点符号**。例如，**Air Twister** 请命名为 `AirTwister`。
- 然后是应用版本号，用 **下划线** 分隔。例如，`AirTwister_1.4.0`。
- 对于注入的插件，请写明插件名称和版本号，并用 **下划线** 分隔。
- 如果不知道注入插件的名称和版本号，只知道是破解版，请写成 `Pro`。如果仅仅是砸壳，什么都不加。
- 应用程序名称、版本号和插件信息均由 **下划线** 连接。本仓库不在末尾加任何标记。

### 一些例子

`Air Twister（仅砸壳）：AirTwister_1.4.0.ipa`

## Structure reference

Repo layout and `apps.json` generation follow [OwO-Network/Repo](https://github.com/OwO-Network/Repo), except no trailing brand tag is appended to file names.
