from cmdi import CmdResult, print_summary


def test_print_summary(capfd):

    # CmdResult
    result = CmdResult(
        val='foo',
        code=1,
        name='foo',
        status='Error',
        color=1,
        out=None,
        err=None
    )

    print_summary(result)

    out, err = capfd.readouterr()
