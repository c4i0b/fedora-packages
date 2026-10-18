/* PCRE1 API subset over PCRE2 — enough for ccze (upstream is dead, and
 * PCRE1 is gone from newer distros). Covers exactly what ccze calls:
 * pcre_compile, pcre_study (no-op), pcre_exec, pcre_get_substring.
 */
#ifndef CCZE_PCRE2_COMPAT_H
#define CCZE_PCRE2_COMPAT_H

#include <stdlib.h>
#include <string.h>
#define PCRE2_CODE_UNIT_WIDTH 8
#include <pcre2.h>

typedef pcre2_code_8 pcre;
typedef void pcre_extra;

#define PCRE_CASELESS PCRE2_CASELESS
#define PCRE_MULTILINE PCRE2_MULTILINE
#define PCRE_EXTENDED PCRE2_EXTENDED
#define PCRE_DOTALL PCRE2_DOTALL

static inline pcre *pcre_compile(const char *pattern, int options,
                                 const char **errptr, int *erroffset,
                                 const unsigned char *tableptr)
{
  static char errbuf[256];
  int errorcode;
  PCRE2_SIZE erroroffset;
  pcre2_code_8 *code = pcre2_compile_8((PCRE2_SPTR8)pattern,
                                       PCRE2_ZERO_TERMINATED, options,
                                       &errorcode, &erroroffset, NULL);
  (void)tableptr;
  if (code == NULL) {
    pcre2_get_error_message_8(errorcode, (PCRE2_UCHAR8 *)errbuf, sizeof(errbuf));
    if (errptr)
      *errptr = errbuf;
    if (erroffset)
      *erroffset = (int)erroroffset;
  }
  return code;
}

/* Study is optional by definition; PCRE2 needs no extra data */
static inline pcre_extra *pcre_study(pcre *code, int options,
                                     const char **errptr)
{
  (void)code;
  (void)options;
  if (errptr)
    *errptr = NULL;
  return NULL;
}

static inline int pcre_exec(const pcre *code, const pcre_extra *extra,
                            const char *subject, int length, int startoffset,
                            int options, int *ovector, int ovecsize)
{
  pcre2_match_data_8 *md = pcre2_match_data_create_from_pattern_8(code, NULL);
  int rc = pcre2_match_8(code, (PCRE2_SPTR8)subject, length, startoffset,
                         options, md, NULL);
  if (rc >= 0) {
    PCRE2_SIZE *ov = pcre2_get_ovector_pointer_8(md);
    uint32_t pairs = pcre2_get_ovector_count_8(md);
    if (pairs > (uint32_t)(ovecsize / 2))
      pairs = ovecsize / 2;
    for (uint32_t i = 0; i < pairs * 2; i++)
      ovector[i] = (int)ov[i];
    rc = (int)pairs;
  }
  pcre2_match_data_free_8(md);
  (void)extra;
  return rc;
}

static inline int pcre_get_substring(const char *subject, const int *ovector,
                                     int stringcount, int stringnumber,
                                     const char **stringptr)
{
  int len;
  char *buf;

  if (stringnumber < 0 || stringnumber >= stringcount ||
      ovector[2 * stringnumber] < 0)
    return PCRE2_ERROR_NOSUBSTRING;
  len = ovector[2 * stringnumber + 1] - ovector[2 * stringnumber];
  buf = malloc(len + 1);
  if (buf == NULL)
    return PCRE2_ERROR_NOMEMORY;
  memcpy(buf, subject + ovector[2 * stringnumber], len);
  buf[len] = '\0';
  *stringptr = buf;
  return len;
}

#endif /* CCZE_PCRE2_COMPAT_H */
