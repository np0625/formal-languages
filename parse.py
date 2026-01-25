import logging
import sys
#
# Basic Kleene-style REs:
# - alphabet: keep it simple, [a-z0-9]. No escapes, so the operator symbols are not part of the alphabet
# - Operators:
#   - '*', '|', '(', ')'
# - We are leaving out '.', '?', and '+' for now, as these are all expressible as
#   more basic constructs:
#   - '.': (a|b|c|...entire alphabet...) # Wow, that's inconvenient
#   - '?': (a|ε)
#   - '+': (aa*)
#
# So we need to write a grammar for these KREs, let's call them:
# KRE ::= ε
#      | a | b | ... z | 0 | 1 ... 9
#      | KRE KRE
#      | KRE "|" KRE
#      | "(" KRE ")"
#      | KRE "*"
#
# We also need a data structure for storing a parsed RE.
# "re string" -> RE IR -> NFA

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def matcher_aux(s, re, s_idx, re_idx, s_len, re_len, mr):
    saved_s_idx = s_idx
    logger.info(f"TOP: re: {re}; s: {s}")
    while re_idx < re_len:
        cur_re = re[re_idx]
        cur_re_type = cur_re[0]
        cur_re_expr = cur_re[1]
        match cur_re_type:
            case 'literal':
                logger.info('BEGIN literal match')
                if s_idx >= s_len:
                    return (False, s_idx, 0)
                cur_char = s[s_idx]
                if cur_char == cur_re_expr:
                    s_idx += 1
                    re_idx += 1
                    logger.debug(f"Literal match success '{cur_char}'")
                else:
                    logger.debug(f"Literal match fail regex '{cur_re_expr}' vs char '{cur_char}'")
                    retval = (False, s_idx, 0)
                    logger.debug(f"RETURN: {retval}")
                    return retval
            case 'union':
                logger.info(f"BEGIN union match for {cur_re_expr}")
                found_any = False
                max_matched = 0
                for subexpr in cur_re_expr:
                    logger.debug(f"trying union subexpr {subexpr}")
                    found, start, matched = matcher_aux(s, subexpr, s_idx, 0, s_len, len(subexpr), mr)
                    if found:
                        logger.debug(f"found union subexpr {subexpr}")
                        max_matched = max([max_matched, matched])
                    found_any = found_any or found
                if found_any:
                    logger.debug(f"Union match success for {cur_re_expr}")
                    s_idx += max_matched
                    re_idx += 1
                else:
                    logger.debug(f"Union match fail for {cur_re_expr}")
                    retval = (False, saved_s_idx, 0)
                    logger.debug(f"RETURNING: {retval}")
                    return retval
            case 'star':
                logger.info(f"BEGIN star match: {cur_re_expr}")
                found, start, matched = matcher_aux(s, cur_re_expr, s_idx, 0, s_len, len(cur_re_expr), mr)
                if found:
                    logger.debug(f"Star match success '{s[s_idx:(s_idx + matched)]}' for expr '{cur_re_expr}' ")
                    s_idx += matched
                    # try to match the same RE again
                else:
                    logger.debug(f"Star match failed for {cur_re_expr}")
                    re_idx += 1
                    # match failed, move on to the next RE starting from where you were
                    # prior to trying to match the *-expr
            case _:
                logger.info("Whoops NYI")
                retval = (False, 999, 999)
                logger.debug(f"RETURN: {retval}")
                return retval
    retval = (True, saved_s_idx, s_idx - saved_s_idx)
    logger.info(f"RETURNING FINAL TRUE: {retval}")
    return retval


def matcher(re, s):
    match_report = []
    retval, start_idx, n_matched = matcher_aux(s, re, 0, 0, len(s), len(re), match_report)
    print(f"Result: {retval}; start: {start_idx} for {n_matched}: {s[start_idx:(start_idx + n_matched)]} in {s} for {re}")
    return (retval, start_idx, n_matched)


def test_runner(list_of_tests, fun):
    f = []
    for t in list_of_tests:
        logger.debug(f"TEST re: {t[0]} in '{t[1]}'")
        res, n_matched = fun(t[0], t[1])
        if res != t[2]:
            f.append(t)
    if len(f) > 0:
        print(f"Failures: {f}")
    else:
        print("All passed")


def m2(re, s):
    found, length = m2_aux(re, s, 0)
    logger.info(f"Found: {found}! Length: {length} [{re} in '{s}']")
    return (found, length)

def m2_aux(re, s, n):
    logger.debug(f"FUN TOP: re: {{{re}}}; s: '{s}'; n: {n}")
    if not re:
        logger.debug(f"FUN success: RE EXHAUSTED, returning from top: {n}")
        return (True, n)
    if not s:
        logger.debug("FUN OUT OF CHARS - FAIL")
        return (False, 0)
    # Begin work
    cur_re = re[0]
    cur_re_type = cur_re[0]
    cur_re_expr = cur_re[1]
    match cur_re_type:
        case 'literal':
            logger.debug(f"literal: {cur_re_expr}")
            if s[0] == cur_re_expr:
                logger.debug("literal matched")
                return m2_aux(re[1:], s[1:], n + 1)
            else:
                return (False, 0)
        case 'union':
            logger.debug(f"union")
            for subexpr in cur_re_expr:
                found_sub, len_sub_match = m2_aux(subexpr, s, 0)
                if found_sub:
                    found_rest, len_rest_match = m2_aux(re[1:], s[len_sub_match:], 0)
                    if found_rest:
                        logger.debug(f"FUN: returning from union with n = {n + len_rest_match}")
                        return (True, n + len_sub_match + len_rest_match)
            return (False, 0)
        case 'star':
            logger.debug(f"star")
            return (False, 'NYI')
        case _:
            logger.debug(f"NYI: {cur_re_type}")
            return (False, 'NYI - unmatched case type')


print("start")
re_0_tests = (((('literal', 'a'), ), 'a', True,),
              ((('literal', 'a'), ), 'b', False),
              ((('literal', 'a'), ('literal', 'a')), 'aa', True),
              ((('literal', 'a'), ('literal', 'a')), 'ab', False),
              ((('literal', 'a'), ('literal', 'a'), ('literal', 'a')), 'aaaa', True),
              ((('literal', 'a'), ('literal', 'b'), ('literal', 'a'), ('literal', 'b'), ('literal', 'a'), ('literal', 'b')), 'ababab', True),
              ((('literal', 'a'), ('literal', 'b'), ('literal', 'a')), 'abab', True),
              ((('literal', 'a'), ('literal', 'b'), ('literal', 'c')), 'abc', True)
              )

re_union_base = (('union', ((('literal', 'a'), ), (('literal', 'b'), ))), )
re_union_t0 = (('union', ((('literal', 'a'), ('literal', 'b')), (('literal', 'c'), ('literal', 'd')))), )
re_1_tests = (
    (re_union_base, 'a', True),
    (re_union_base, 'b', True),
    (re_union_base, 'ab', True),
    (re_union_base, 'ba', True),
    (re_union_t0, 'ab', True),
    (re_union_t0, 'cd', True),
    (re_union_t0, 'abkk', True),
    (re_union_t0, 'cdkk', True),
    (re_union_t0, 'aab', False),
    (re_union_t0, 'abcd', True),
    (re_union_t0, 'cdab', True),
    (re_union_t0, 'a', False),
    (re_union_t0, 'c', False),
    (re_union_t0, 'ac', False),
    (re_union_t0, 'cb', False),
)

re_lu_t0 = (('literal', 'k'), *re_union_t0, ('literal', '9'))
print(f"re_lu_t0{re_lu_t0}")
# sys.exit()
re_2_tests = (
    (re_lu_t0, 'kab9', True),
    (re_lu_t0, 'kabab9', False),
    (re_lu_t0, 'kcd9', True),
    (re_lu_t0, 'kcdab9', False),
    (re_lu_t0, 'ab9', False),
    (re_lu_t0, 'kcd', False),
    (re_lu_t0, 'k9', False),
    (re_lu_t0, 'cd9', False),
    (re_lu_t0, 'kabcd', False),
    (re_lu_t0, 'kab99', True),

)

# test_runner(re_0_tests, m2)
# test_runner(re_1_tests, m2)
test_runner(re_2_tests, m2)
sys.exit()

# re1 = "a(d|e)"
re1 = (('literal', 'a'), ('union', (('literal', 'd'), ('literal', 'e'))))
# re2 = f(qp)*
re2 = (('literal', 'f'), ('star', (('literal', 'q'), ('literal', 'p'))))
# re3 = (ab)*(p|q)(x|y)*z
re3 = (('star', (('literal', 'a'), ('literal', 'b'))),
       ('union', (('literal', 'p'), ('literal', 'q'))),
       ('star', (('union',
                     (('literal', 'x'), ('literal', 'y'))), )),
       ('literal', 'z')
       )
# re4 = (x|y)*z
re4 = (('star', (('union',
                     (('literal', 'x'), ('literal', 'y'))), )),
       ('literal', 'z')
       )
# re5 = (ab)*
re5 = (('star', (('literal', 'a'), ('literal', 'b'))), )
# re6 = (a|b)
re6 = (('union', (('literal', 'a'), ('literal', 'b'))), )
re7 = (('literal', 'd'), ('literal', 'f'), ('literal', 'a'), ('literal', 'g'))
re8 = (('union',
        (
            (('literal', 'd'), ('literal', 'f'), ('literal', 'g')),
            (('literal', 'd'), ('literal', 'f'), ('literal', 'g'), ('literal', 'g')),
            (('literal', 'd'), ('literal', 'f'), ('literal', 'g'), ('literal', 'a')),
            (('literal', 'd'), ('literal', 'f'), ('literal', 'g'), ('literal', 'a'),
             ('literal', 'g'), ('literal', 'g')),
            (('literal', 'd'), ),
            (('literal', 'a'), ('literal', 'b'))
        )
        ), )
re9 = (('literal', 'a'), ('star', (('literal', 'b'), )), ('literal', 'c'))
# re10 = (ab|cd)k(de)*
re10 = (
    ('union', (
        (('literal', 'a'), ('literal', 'b')),
        (('literal', 'c'), ('literal', 'd'))
    )),
    ('literal', 'k'),
    ('star', (('literal', 'd'), ('literal', 'e')))
)
# re11 = (ab|cd|(mq)*)k(de)*
re11 = (
    ('union', (
        (('literal', 'a'), ('literal', 'b')),
        (('literal', 'c'), ('literal', 'd')),
        (('star', (('literal', 'm'), ('literal', 'q'))), )
    ), ),
    ('literal', 'k'),
    ('star', (('literal', 'd'), ('literal', 'e')))
)
re12 = (('star', (('literal', 'x'), )), ('literal', 'a'))
re13 = (('star', (('literal', 'x'), ('literal', 'z'))), ('literal', 'a'))
# matcher(re8, 'dfgaggg')
# matcher(re9, 'ac')
# matcher(re10, 'abkdedededede')
# matcher(re11, 'kde')
# matcher(re12, 'xxxxaaaa')

# re14 = x(a|b)(zap)*9
re14 = (('literal', 'x'), ('union', ((('literal', 'a'), ), (('literal', 'b'), ))),
        ('star', (('literal', 'z'), ('literal', 'a'), ('literal', 'p'))), ('literal', '9'))
do_14 = False
if do_14:
    re14_testers = ('xazap9', 'xbzap9', 'xa9', 'xb9', 'xazapzap9', 'xbzapzapzapzapzap9')
    re14_results = [t[0] for t in [matcher(re14, x) for x in re14_testers ]]
    if False in re14_results:
        print("PROBLEM!!!")
    else:
        print("All re14 results passed")

# re15 and re16 both incorrectly fail because of lack of backtracking.
re15 = (('star', (('literal', 'a'), )), ('literal', 'a'))
re16 = (('union', ((('literal', 'a'), ), (('literal', 'a'), ('literal', 'b')))),
        ('literal', 'b'))
# print(matcher(re15, 'aa'))
# print(matcher(re16, 'ab'))

print(m2(re14, 'ab'))
# Note cur behaviour is that trailing input is ignored once a match is found
print("end")
