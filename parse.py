import logging

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
    chars_matched = 0
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
                    chars_matched += 1
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
                    chars_matched += max_matched
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
                    chars_matched += matched
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
    retval = (True, saved_s_idx, chars_matched)
    logger.info(f"RETURNING FINAL TRUE: {retval}")
    return retval


def matcher(re, s):
    match_report = []
    retval, start_idx, n_matched = matcher_aux(s, re, 0, 0, len(s), len(re), match_report)
    print(f"Result: {retval}; start: {start_idx} for {n_matched}: {s[start_idx:(start_idx + n_matched)]} in {s} for {re}")
    return (retval, start_idx, n_matched)

print("start")
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
matcher(re11, 'kde') # WRONG: re11 isn't matching "kde..."!
# matcher(re12, 'xxxxaaaa')

# re14 = x(a|b)(zap)*9
do_14 = True
if do_14:
    re14 = (('literal', 'x'), ('union', ((('literal', 'a'), ), (('literal', 'b'), ))),
            ('star', (('literal', 'z'), ('literal', 'a'), ('literal', 'p'))), ('literal', '9'))
    re14_testers = ('xazap9', 'xbzap9', 'xa9', 'xb9', 'xazapzap9', 'xbzapzapzapzapzap9')
    re14_results = [t[0] for t in [matcher(re14, x) for x in re14_testers ]]
    if False in re14_results:
        print("PROBLEM!!!")
    else:
        print("All re14 results passed")

re15 = (('star', (('literal', 'a'), )), ('literal', 'a'))
print(matcher(re15, 'aaa'))
# Note cur behaviour is that trailing input is ignored once a match is found
print("end")
