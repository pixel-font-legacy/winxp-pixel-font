import json
import shutil
from collections.abc import Sequence
from zipfile import ZipFile

from loguru import logger

from tools import configs
from tools.configs import path_define
from tools.configs.options import FontFormat
from tools.services.font_service import DumpLog


def make_release_zips(dump_logs: Sequence[DumpLog], font_formats: Sequence[FontFormat]) -> None:
    path_define.RELEASES_DIR.mkdir(parents=True, exist_ok=True)

    for font_format in font_formats:
        file_path = path_define.RELEASES_DIR.joinpath(f'winxp-pixel-font-{font_format}-v{configs.VERSION}.zip')
        with ZipFile(file_path, 'w') as file:
            file.write(path_define.PROJECT_ROOT_DIR.joinpath('LICENSE-FONT.md'), 'README.md')
            for dump_log in dump_logs:
                for font_size in dump_log.font_sizes:
                    file_path = path_define.OUTPUTS_DIR.joinpath(f'{dump_log.font_name}-{font_size}px.{font_format}')
                    file.write(file_path, file_path.name)
        logger.info("Make release zip: '{}'", file_path)


def update_www(dump_logs: Sequence[DumpLog]) -> None:
    if path_define.WWW_FONTS_DIR.exists():
        shutil.rmtree(path_define.WWW_FONTS_DIR)
    path_define.WWW_FONTS_DIR.mkdir(parents=True)

    for path_from in path_define.OUTPUTS_DIR.iterdir():
        if not path_from.name.endswith('.otf.woff2'):
            continue
        path_to = path_from.copy_into(path_define.WWW_FONTS_DIR)
        logger.info("Copy file: '{}' -> '{}'", path_from, path_to)

    db_file_path = path_define.WWW_FONTS_DIR.joinpath('db.js')
    db_file_path.write_text(f'export default {json.dumps([dump_log.__dict__ for dump_log in dump_logs], indent=4, ensure_ascii=False)}\n', 'utf-8')
    logger.info("Build: '{}'", db_file_path)

    css_file_path = path_define.WWW_FONTS_DIR.joinpath('index.css')
    with css_file_path.open('w', encoding='utf-8') as file:
        for dump_log in dump_logs:
            for font_size in dump_log.font_sizes:
                file.write('\n')
                file.write('@font-face {\n')
                file.write(f'    font-family: "{dump_log.family_name} {font_size}px";\n')
                file.write(f'    src: url("{dump_log.font_name}-{font_size}px.otf.woff2");\n')
                file.write('}\n')
    logger.info("Build: '{}'", css_file_path)
