# The command line

`pip install sil-lift[cli]` provides the `sil-lift` command — a small
LiftTools-style utility (and a worked example of the library API).

```
sil-lift validate PATH        all problems, entry/line-addressed; exit 1 on errors
sil-lift stats PATH           entry/sense/language counts (streaming; any size)
sil-lift sort PATH [-o OUT]   canonically sorted, diff-ready copy (default: in place)
sil-lift check-media PATH     missing and orphaned media report; exit 1 if missing
```

Examples:

```
$ sil-lift validate dictionary.lift
error [dangling-ref] dictionary.lift:88 (entry apu): ref 'nope' matches no entry id/guid or sense id
warning [uri-not-rfc] dictionary.lift:6: <range href='file://C:/...'>: Windows drive letter used as URI authority (FLEx-style file://C:/)
1 error(s), 1 warning(s)

$ sil-lift stats sango.lift
entries:   3507
senses:    4238
...
```

Exit codes: `0` success (warnings allowed), `1` findings (validation errors /
missing media), `2` unreadable input.
