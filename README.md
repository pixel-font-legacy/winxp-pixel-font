> [!WARNING]
>
> 本字体并非公有领域，您在使用时，请务必谨慎考量并自负版权风险。

# Windows XP 像素字体

[![Releases](https://img.shields.io/github/v/release/pixel-font-legacy/winxp-pixel-font?style=flat-square)](https://github.com/pixel-font-legacy/winxp-pixel-font/releases)

Windows XP 系统的点阵字体，提取自 Windows XP SP3 x86 官方镜像。

原始字体的点阵数据基于内嵌的 [OpenType - EBDT](https://learn.microsoft.com/en-us/typography/opentype/spec/ebdt) 数据格式，其点阵字形在现代系统中使用起来不太方便。

这个项目进行了如下工作：

1. 将原始字体中的每个点阵尺寸各拆分为一个独立字体。
2. 将原始的点阵数据转换为轮廓字形。

## 程序依赖

- [Pixel Font Builder](https://github.com/TakWolf/pixel-font-builder)
- [Pixel Font Knife](https://github.com/TakWolf/pixel-font-knife)
- [FontTools](https://github.com/fonttools/fonttools)
- [Loguru](https://github.com/Delgan/loguru)
- [Cyclopts](https://github.com/BrianPugh/cyclopts)
- [Vue](https://vuejs.org)

## 许可证

### 字体

本字体并非公有领域，您在使用时，请务必谨慎考量并自负版权风险。

原始字体提取自 Windows XP SP3 x86 官方镜像，版权归属于原相关制作公司。

字体在转换的过程中，保留了原始字体的元信息。

### 构建程序

使用 [「MIT 许可证」](LICENSE-MIT) 授权。
