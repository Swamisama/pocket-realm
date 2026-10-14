#pragma once
#include_next <paths.h>
#undef _PATH_TMP
// Preserve the recovered helper's path; only its ELF alignment changes.
#define _PATH_TMP "/data/data/com.termux/files/usr/tmp/"
