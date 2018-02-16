import sys
import os
from typing import Union
from cmdi import CmdResult, print_summary
from buildlib import yaml, semver, build, git


CFG_FILE = 'Project'
CFG = yaml.loadfile(
    file=CFG_FILE,
    keep_order=True
)

__version__ = CFG.get('version')


def build_wheel(
) -> Union[CmdResult, None]:
    """"""
    return build.cmd.build_python_wheel(
        clean_dir=True,
    )


def push_registry(
) -> Union[CmdResult, None]:
    """"""
    return build.cmd.push_python_wheel_to_pypi(
        clean_dir=True,
    )


def bump_version() -> Union[CmdResult, None]:
    """
    Bump (update) version number in CONFIG.yaml.
    """
    new_version: str = semver.prompt.semver_num_by_choice(
        cur_version=CFG.get('version')
    )

    return build.cmd.update_version_num_in_cfg(
        config_file=CFG_FILE,
        semver_num=new_version,
    )


def bump_git() -> None:
    """"""
    results = []
    version_bumped = False

    if build.prompt.should_update_version(
        default='y',
    ):
        bump_version()
        version_bumped = True

    seq_settings = git.seq.get_settings_from_user(
        should_tag_default=version_bumped,
        should_bump_any=True,
        version=CFG.get('version'),
    )

    results.extend(git.seq.bump_sequence(seq_settings))

    print_summary(results)


def bump_all() -> None:
    """"""
    results = []
    version_was_bumped = False

    if build.prompt.should_update_version(
        default='y'
    ):
        bump_version()
        version_was_bumped = True

    should_build_wheel: bool = build.prompt.should_build_wheel(
        default='y',
    )

    should_push_registry: bool = build.prompt.should_push_pypi(
        default='y' if version_was_bumped else 'n',
    )

    git_settings = git.seq.get_settings_from_user(
        should_tag_default=version_was_bumped,
        version=CFG.get('version'),
    )

    if should_build_wheel:
        results.append(build.cmd.build_python_wheel(
            clean_dir=True,
        ))

    if git_settings.should_bump_any:
        results.extend(git.seq.bump_sequence(git_settings))

    if should_push_registry:
        results.append(build.cmd.push_python_wheel_to_pypi(
            clean_dir=True,
        ))

    print_summary(results)
