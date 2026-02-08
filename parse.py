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


def match(re, s):
    found, length = match_aux(re, s, 0)
    return (found, length)

def match_aux(re, s, n):
    if not re:
        return (True, n)
    cur_re = re[0]
    cur_re_type = cur_re[0]
    cur_re_expr = cur_re[1]
    match cur_re_type:
        case 'literal':
            if not s:
                return (False, 0)
            if s[0] == cur_re_expr:
                return match_aux(re[1:], s[1:], n + 1)
            else:
                return (False, 0)
        case 'union':
            for subexpr in cur_re_expr: # Try matches in the order that subexpressions occur
                found_sub, len_sub_match = match_aux(subexpr, s, 0)
                # If the subexpression matches, try the rest of the RE.
                # If the remainder doesn't match, try again with the next subexpr
                if found_sub:
                    found_rest, len_rest_match = match_aux(re[1:], s[len_sub_match:], 0)
                    if found_rest:
                        n_matched = n + len_sub_match + len_rest_match
                        return (True, n_matched)
            # If we reach here, it means the RE can't be matched with any of the subexprs
            return (False, 0)
        case 'star':
            offsets = [0]
            while True:
                found, len_match = match_aux(cur_re_expr, s[offsets[-1]:], 0)
                if not found or len_match == 0:
                    break
                else:
                    offsets.append(offsets[-1] + len_match)
            while offsets:
                offset = offsets.pop()
                found, len_match = match_aux(re[1:], s[offset:], 0)
                if found:
                    return (True, n + offset + len_match)
                else:
            return (False, 0)
        case _:
            raise Exception(f"RE type {cur_re_type} not implemented")

def run_tests(list_of_tests, fun):
    f = []
    for t in list_of_tests:
        logger.debug(f"TEST re: {t[0]} in '{t[1]}'")
        res, n_matched = fun(t[0], t[1])
        if res != t[2]:
            f.append(t)
    if len(f) > 0:
        print(f"🔥 🔥 🔥 __result__: Failures: {f}")
    else:
        print("🪷 __result__: All passed")


def m2(re, s):
    found, length = m2_aux(re, s, 0)
    logger.info(f"Found: {found} {'✅' if found else '❌'}! Length: {length} [{re} in '{s}']")
    return (found, length)

def m2_aux(re, s, n):
    logger.debug(f"FUN TOP: re: {{{re}}}; s: '{s}'; n: {n}")
    if not re:
        logger.debug(f"FUN success: RE EXHAUSTED, returning from top: {n}")
        return (True, n)
    # Begin work
    cur_re = re[0]
    cur_re_type = cur_re[0]
    cur_re_expr = cur_re[1]
    match cur_re_type:
        case 'literal':
            logger.debug(f"LITERAL: {cur_re_expr}")
            if not s:
                logger.debug("  LITERAL: FUN OUT OF CHARS - FAIL")
                return (False, 0)
            if s[0] == cur_re_expr:
                logger.debug("  LITERAL matched")
                return m2_aux(re[1:], s[1:], n + 1)
            else:
                logger.debug(f"  LITERAL not matched: got {s[0]}")
                return (False, 0)
        case 'union':
            logger.debug(f"UNION: {cur_re_expr} ")
            # Try matches in the order that subexpressions occur
            for subexpr in cur_re_expr:
                found_sub, len_sub_match = m2_aux(subexpr, s, 0)
                # If the subexpression matches, try the rest of the RE.
                # If the remainder doesn't match, try again with the next subexpr
                if found_sub:
                    found_rest, len_rest_match = m2_aux(re[1:], s[len_sub_match:], 0)
                    if found_rest:
                        n_matched = n + len_sub_match + len_rest_match
                        logger.debug(f"FUN: returning from union with n = {n_matched}")
                        return (True, n_matched)
            # If we reach here, it means the RE can't be matched with any of the subexprs
            return (False, 0)
        case 'star':
            logger.debug(f"STAR: {cur_re_expr}")
            logger.debug(f"  STAR: starting greedy matching")
            offsets = [0]
            while True:
                found, len_match = m2_aux(cur_re_expr, s[offsets[-1]:], 0)
                if not found or len_match == 0:
                    logger.debug(f"  STAR: not found at '{s[offsets[-1]:]}'")
                    break
                else:
                    logger.debug(f"  STAR: found at '{s[offsets[-1]:]}'")
                    offsets.append(offsets[-1] + len_match)
                    logger.debug(f"  STAR: offsets so far: {offsets}")
            # Ok, matched as much as possible
            logger.debug(f"  STAR: starting post-greedy matching phase w/ offset array: {offsets}")
            while offsets:
                offset = offsets.pop()
                found, len_match = m2_aux(re[1:], s[offset:], 0)
                if found:
                    logger.debug(f"  STAR: matched remaining RE {re[1:]} against '{s[offset:]}'")
                    return (True, n + offset + len_match)
                else:
                    logger.debug(f"  STAR: couldn't match remaining RE {re[1:]} against '{s[offset:]}'")
            logger.debug(f"  STAR: not able to match rest of RE {re[1:]} against '{s}'")
            return (False, 0)
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
re_union_t1 = (('union', (
    (('literal', 'a'), ),
    (('literal', 'a'), ('literal', 'b')),
)), )
re_union_t2 = (('union', (
    (('literal', 'a'), ('literal', 'b')),
    (('literal', 'a'), ),
)), )
re_union_t3 = (('union', (
    (('literal', 'a'), ('literal', 'b')),
    (('literal', 'a'), ('literal', 'a')),
    (('literal', 'a'), ),
    (('literal', 'b'), ),
    ), ), )

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

# re_lu_t0 = k(ab|cd)9
re_lu_t0 = (('literal', 'k'), *re_union_t0, ('literal', '9'), )
# re_lu_t1 = (a|ab)b
re_lu_t1 = (*re_union_t1, ('literal', 'b'), )
# re_lu_t1 = (ab|a)b
re_lu_t2 = (*re_union_t2, ('literal', 'b'), )
# re_lu_t3 = x(ab|a)ab(ab|cd)cd
re_lu_t3 = (('literal', 'x'), *re_union_t2, ('literal', 'a'), ('literal', 'b'), *re_union_t0, ('literal', 'c'), ('literal', 'd'), )
# re_lu_t4 = (ab|aa|a|b)ab(ab|abcd)cd
re_lu_t4 = (*re_union_t3,
            ('literal', 'a'), ('literal', 'b'),
            ('union', ((('literal', 'a'), ('literal', 'b')),
                        (('literal', 'a'), ('literal', 'b'), ('literal', 'c'), ('literal', 'd'))), ),
            ('literal', 'c'), ('literal', 'd'), )
# print(f"re_lu_t2{re_lu_t2}")

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

re_3_tests = (
    (re_lu_t1, 'ab', True),
    (re_lu_t1, 'abb', True),
    (re_lu_t1, 'aba', True), # Yes, because ab is a match, and the additional a is just left over input
    (re_lu_t1, 'aab', False),
)

re_4_tests = (
    (re_lu_t2, 'ab', True),
    (re_lu_t2, 'abb', True),
    (re_lu_t2, 'aba', True), # Yes, because ab is a match, and the additional a is just left over input
    (re_lu_t2, 'aab', False),
)

re_5_tests = (
    (re_lu_t3, 'xabababcd', True),
    (re_lu_t3, 'xabababacd', False),
    (re_lu_t3, 'xaabcd', False),
    (re_lu_t3, 'xaabcdcd', True),
    (re_lu_t3, 'xaababcd', True),
)

# re_lu_t4 = (ab|aa|a|b)ab(ab|abcd)cd
re_6_tests = (
    (re_lu_t4, 'abababcd', True),
    (re_lu_t4, 'aababcd', True),
    (re_lu_t4, 'bababcdcd', True),
    (re_lu_t4, 'aaababcd', True),
    (re_lu_t4, 'aababcdcd', True), # will match short (first 7)

    )

re_star_0 = (('star', (('literal', 'a'), )), ('literal', 'b'))
re_star_1 = (('star', (('literal', 'a'), )), ('literal', 'a'))
re_7_tests = (
    (re_star_0, 'ab', True),
    (re_star_0, 'aaaab', True),
    (re_star_0, 'b', True),
    (re_star_1, 'a', True),
    (re_star_1, 'aa', True),
    (re_star_1, 'aaaaaaaa', True),
    (re_star_1, 'aaaaaaaabbbb', True),
)




# re1 = "a(d|e)"
re1 = (('literal', 'a'), ('union', (('literal', 'd'), ('literal', 'e'))))
# re_star_2 = f(qp)*
re_star_2 = (('literal', 'f'), ('star', (('literal', 'q'), ('literal', 'p'))))
# re_star_3 = (ab)*(p|q)(x|y)*z
re_star_3 = (('star', (('literal', 'a'), ('literal', 'b'))),
       ('union', (
           (('literal', 'p'),),
           (('literal', 'q'), )),
        ),
       ('star', (('union', (
           (('literal', 'x'), ),
           (('literal', 'y'), ),
         )),)
        ),
       ('literal', 'z'),
       )

# re_star_4 = x(ab)*ababab
re_star_4 = (
    ('literal', 'x'),
    ('star', (('literal', 'a'), ('literal', 'b'))),
    ('literal', 'a'), ('literal', 'b'), ('literal', 'a'), ('literal', 'b'), ('literal', 'a'), ('literal', 'b'),
)
# re4 = (x|y)*z
re4 = (('star', (('union',
                     (('literal', 'x'), ('literal', 'y'))), )),
       ('literal', 'z')
       )

# re_star_2 = f(qp)*
re_8_tests = (
    (re_star_2, 'fqp', True),
    (re_star_2, 'ffqp', True), # yes, because f matches f, and the remainder of the string is a non-match for (qp)*
    (re_star_2, 'qp', False),
    (re_star_2, 'f', True),
    (re_star_2, 'fa', True),
)

# re_star_3 = (ab)*(p|q)(x|y)*z
re_9_tests = (
    (re_star_3, 'abpxz', True),
    (re_star_3, 'abababqxxxyxyxyxyyyyyxxxxyyxyxyxxyz', True),
    (re_star_3, 'pz', True),
)

re_10_tests = (
    (re_star_4, 'xabababababababababababab', True),
)

# p01 = a|ab|cd|(mq)*
re_big_p01 = (('union', (
    (('literal', 'a')),
    (('literal', 'a'), ('literal', 'b')),
    (('literal', 'c'), ('literal', 'd')),
    (('star', (('literal', 'm'), ('literal', 'q'))), ),
)), )
# p02 = ((map|pam)*|(human|room)*)*
re_big_p02_lit01 = (('literal', 'm'), ('literal', 'a'), ('literal', 'p'))
re_big_p02_lit02 = (('literal', 'p'), ('literal', 'a'), ('literal', 'm'))
re_big_p03_lit01 = (('literal', 'h'), ('literal', 'u'), ('literal', 'm'), ('literal', 'a'), ('literal', 'n'))
re_big_p03_lit02 = (('literal', 'r'), ('literal', 'o'), ('literal', 'o'), ('literal', 'm'))

re_big_p04_lit = (('literal', 'm'), ('literal', 'a'), ('literal', 'p'), ('literal', 'p'), ('literal', 'a'), ('literal', 'm'), ('literal', 'h'), ('literal', 'u'), ('literal', 'm'), ('literal', 'a'), ('literal', 'n'), ('literal', 'r'), ('literal', 'o'), ('literal', 'o'), ('literal', 'm'))


re_big_p02 = (('star',
               (('union', ((('star', (('union', (re_big_p02_lit01, re_big_p02_lit02)), )), ),
                           (('star', (('union', (re_big_p03_lit01, re_big_p03_lit02)), )), )),
                 ),
                )), )

rex_big_p02 = (('star',
               (('union', ((('star', (('union', (re_big_p03_lit01, re_big_p03_lit02)), )), ),
                           (('star', (('union', (re_big_p02_lit01, re_big_p02_lit02)), )), )),
                 ),
                )), )

re_simple_union = (('union', (re_big_p02_lit01, re_big_p03_lit02)), )
re_star_of_union = (('star', re_simple_union), )

re_s2 = (('star', (('literal', 'a'), )), )
re_s2_double = (('star', re_s2), )
re_s2_triple = (('star', re_s2_double), )

# run_tests(re_0_tests, m2)
# run_tests(re_1_tests, m2)
# run_tests(re_2_tests, m2)
# run_tests(re_3_tests, m2)
# run_tests(re_4_tests, m2)
# run_tests(re_5_tests, m2)
# run_tests(re_6_tests, m2)
# run_tests(re_7_tests, m2)
# run_tests(re_8_tests, m2)
# run_tests(re_9_tests, m2)
# run_tests(re_10_tests, m2)
# sys.exit()
# m2(re_big_p01, 'mqmqmqmqmq')
# m2(re_big_p02_lit01, 'map')
#m2(re_big_p02_lit02, 'pam')
#m2(re_big_p03_lit01, 'human')
#m2(re_big_p03_lit02, 'room')
#m2(re_big_p04_lit, 'mappamhumanroom')
# m2(re_big_p02, 'map')



while True:
    s = input("input: ").strip()
    m2(re_star_of_union, s)

sys.exit()

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
