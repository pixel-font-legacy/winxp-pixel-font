import itertools
from datetime import datetime

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.BitmapGlyphMetrics import SmallGlyphMetrics, BigGlyphMetrics
from fontTools.ttLib.tables.E_B_D_T_ import table_E_B_D_T_, ebdt_bitmap_classes, ebdt_bitmap_format_5, ebdt_bitmap_format_8, ebdt_bitmap_format_9
from fontTools.ttLib.tables.E_B_L_C_ import table_E_B_L_C_
# noinspection PyProtectedMember
from fontTools.ttLib.tables._n_a_m_e import table__n_a_m_e
from loguru import logger
from pixel_font_builder import FontBuilder, Glyph, opentype
from pixel_font_knife.mono_bitmap import MonoBitmap

from tools import configs
from tools.configs import path_define
from tools.configs.options import FontFormat


class DumpLog:
    family_name: str
    font_name: str
    font_sizes: list[int]

    def __init__(
            self,
            family_name: str,
            font_name: str,
    ):
        self.family_name = family_name
        self.font_name = font_name
        self.font_sizes = []


def dump_fonts(font_formats: list[FontFormat]) -> list[DumpLog]:
    path_define.outputs_dir.mkdir(parents=True, exist_ok=True)

    dump_logs = []
    for dump_config in configs.dump_configs:
        for sub_config in dump_config.sub_configs:
            tt_font = TTFont(dump_config.font_file_path, fontNumber=sub_config.font_number)
            tb_name: table__n_a_m_e = tt_font['name']
            tb_eblc: table_E_B_L_C_ = tt_font['EBLC']
            tb_ebdt: table_E_B_D_T_ = tt_font['EBDT']

            dump_log = DumpLog(tb_name.getDebugName(1), sub_config.font_name)

            for strike, strike_data in zip(tb_eblc.strikes, tb_ebdt.strikeData):
                assert strike.bitmapSizeTable.ppemX == strike.bitmapSizeTable.ppemY
                assert strike.bitmapSizeTable.bitDepth == 1

                builder = FontBuilder()

                builder.font_metric.font_size = strike.bitmapSizeTable.ppemY
                builder.font_metric.horizontal_layout.ascent = strike.bitmapSizeTable.hori.ascender
                builder.font_metric.horizontal_layout.descent = strike.bitmapSizeTable.hori.descender
                builder.font_metric.vertical_layout.ascent = strike.bitmapSizeTable.vert.ascender
                builder.font_metric.vertical_layout.descent = strike.bitmapSizeTable.vert.descender

                # Fix incorrect descent
                if builder.font_metric.horizontal_layout.descent > 0:
                    builder.font_metric.horizontal_layout.descent *= -1
                if builder.font_metric.vertical_layout.descent > 0:
                    builder.font_metric.vertical_layout.descent *= -1

                builder.meta_info.version = f'{tb_name.getDebugName(5)} - Dump {configs.version}'
                builder.meta_info.created_time = datetime.fromisoformat(f'{configs.version.replace('.', '-')}T00:00:00Z')
                builder.meta_info.modified_time = builder.meta_info.created_time
                builder.meta_info.family_name = f'{tb_name.getDebugName(1)} {builder.font_metric.font_size}px'
                builder.meta_info.weight_name = sub_config.weight_name
                builder.meta_info.serif_style = sub_config.serif_style
                builder.meta_info.slant_style = sub_config.slant_style
                builder.meta_info.width_style = sub_config.width_style
                builder.meta_info.manufacturer = tb_name.getDebugName(8)
                builder.meta_info.designer = tb_name.getDebugName(9)
                builder.meta_info.description = tb_name.getDebugName(10)
                builder.meta_info.copyright_info = tb_name.getDebugName(0)
                builder.meta_info.license_info = tb_name.getDebugName(13)
                builder.meta_info.vendor_url = tb_name.getDebugName(11)
                builder.meta_info.designer_url = tb_name.getDebugName(12)
                builder.meta_info.license_url = tb_name.getDebugName(14)

                glyph_infos = {}
                for index_sub_table in strike.indexSubTables:
                    for glyph_name in index_sub_table.names:
                        assert glyph_name not in glyph_infos
                        bitmap_data = strike_data[glyph_name]
                        assert isinstance(bitmap_data, ebdt_bitmap_classes[index_sub_table.imageFormat])

                        if isinstance(bitmap_data, ebdt_bitmap_format_5):
                            metrics = index_sub_table.metrics
                        else:
                            metrics = bitmap_data.metrics

                        if isinstance(bitmap_data, (ebdt_bitmap_format_8, ebdt_bitmap_format_9)):
                            bitmap = None
                            components = bitmap_data.componentArray
                        else:
                            bitmap = []
                            for row_n in range(metrics.height):
                                row_bytes = bitmap_data.getRow(row_n, bitDepth=strike.bitmapSizeTable.bitDepth, metrics=metrics)
                                row_string = ''
                                for b in row_bytes:
                                    row_string += f'{b:08b}'
                                bitmap.append([int(c) for c in row_string])
                            components = None

                        glyph_infos[glyph_name] = {
                            'image_format': index_sub_table.imageFormat,
                            'metrics': metrics,
                            'bitmap': bitmap,
                            'components': components,
                        }

                glyph_names = set()
                for code_point, glyph_name in sorted(itertools.chain([(-1, '.notdef')], tt_font.getBestCmap().items())):
                    if glyph_name not in glyph_infos and glyph_name != '.notdef':
                        continue

                    if code_point != -1:
                        builder.character_mapping[code_point] = glyph_name

                    if glyph_name in glyph_names:
                        continue
                    glyph_names.add(glyph_name)

                    if glyph_name not in glyph_infos:
                        assert glyph_name == '.notdef'
                        builder.glyphs.append(Glyph(
                            name='.notdef',
                            advance_width=builder.font_metric.font_size,
                            advance_height=builder.font_metric.font_size,
                        ))
                        continue

                    glyph_info = glyph_infos[glyph_name]
                    image_format = glyph_info['image_format']
                    metrics = glyph_info['metrics']

                    if isinstance(metrics, SmallGlyphMetrics):
                        if strike.bitmapSizeTable.flags == 1:  # Horizontal
                            hori_bearing_x = metrics.BearingX
                            hori_bearing_y = metrics.BearingY
                            hori_advance = metrics.Advance
                            vert_bearing_x = 0
                            vert_bearing_y = 0
                            vert_advance = 0
                        else:  # Vertical
                            assert strike.bitmapSizeTable.flags == 2
                            hori_bearing_x = 0
                            hori_bearing_y = 0
                            hori_advance = 0
                            vert_bearing_x = metrics.BearingX
                            vert_bearing_y = metrics.BearingY
                            vert_advance = metrics.Advance
                    else:
                        assert isinstance(metrics, BigGlyphMetrics)
                        hori_bearing_x = metrics.horiBearingX
                        hori_bearing_y = metrics.horiBearingY
                        hori_advance = metrics.horiAdvance
                        vert_bearing_x = metrics.vertBearingX
                        vert_bearing_y = metrics.vertBearingY
                        vert_advance = metrics.vertAdvance

                    if image_format in (8, 9):
                        components = glyph_info['components']
                        assert components is not None

                        mono_bitmap = MonoBitmap.create(metrics.width, metrics.height)
                        for component in components:
                            component_bitmap = glyph_infos[component.name]['bitmap']
                            assert component_bitmap is not None
                            mono_bitmap = mono_bitmap.plus(MonoBitmap(component_bitmap), x=component.xOffset, y=component.yOffset)
                        bitmap = mono_bitmap.data
                    else:
                        bitmap = glyph_info['bitmap']
                        assert bitmap is not None

                    builder.glyphs.append(Glyph(
                        name=glyph_name,
                        horizontal_offset=(hori_bearing_x, hori_bearing_y - metrics.height),
                        advance_width=hori_advance,
                        vertical_offset=(vert_bearing_x, vert_bearing_y),
                        advance_height=vert_advance,
                        bitmap=bitmap,
                    ))

                for font_format in font_formats:
                    file_path = path_define.outputs_dir.joinpath(f'{sub_config.font_name}-{builder.font_metric.font_size}px.{font_format}')
                    match font_format:
                        case 'otf.woff':
                            builder.save_otf(file_path, flavor=opentype.Flavor.WOFF)
                        case 'otf.woff2':
                            builder.save_otf(file_path, flavor=opentype.Flavor.WOFF2)
                        case 'ttf.woff':
                            builder.save_ttf(file_path, flavor=opentype.Flavor.WOFF)
                        case 'ttf.woff2':
                            builder.save_ttf(file_path, flavor=opentype.Flavor.WOFF2)
                        case _:
                            getattr(builder, f'save_{font_format}')(file_path)
                    logger.info("Make font: '{}'", file_path)

                dump_log.font_sizes.append(builder.font_metric.font_size)

            dump_log.font_sizes.sort()
            dump_logs.append(dump_log)
    return dump_logs
