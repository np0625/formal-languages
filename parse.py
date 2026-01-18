#
# Parts of text:
# 1. Title (only one)
# 2. Header (many)
# 3. Sentence
# 4. Inter-word break
# 5. Paragraph
# 6. Inter-paragraph break
# 7. Section
# 8. Inter-section break
# 9. Word
# 9.1 Identifier (a reference or a gene name)
# 10. Sentence ender (periods)
# 11. Other punctuation (commas, semicolons, dashes, colons, ...)
# 12. "Whole Text"

s = """All of the graph‐based reasoning converges on a single candidate—Betamethasone—as a putative therapy for Leber hereditary optic neuropathy (LHON).  The chains fall into three thematic clusters:

“Interaction → p53” paths
• Betamethasone is said to “interact with” a panel of unrelated small molecules (dactinomycin, fenofibrate, selumetinib, etc.).
• Each partner molecule has literature linking it to modulation of TP53.
• A Japanese case–control study (PMID 15838728) shows that a TP53 Arg72 polymorphism modifies age of LHON onset, providing a legitimate TP53–LHON association.

Weaknesses:
– No evidence is offered that Betamethasone itself alters TP53; the graph relies on an “interacts-with” edge that is typically derived from co-administration records or in-vitro binding screens, not a causal pharmacodynamic effect.
– The TP53 polymorphism is a disease modifier, not a therapeutic target; lowering or raising p53 activity has never been shown to rescue mitochondrial complex-I dysfunction that drives LHON.

Glucocorticoid‐receptor & acetylcholinesterase paths
• Betamethasone, as a corticosteroid, binds NR3C1 (glucocorticoid receptor).  NR3C1 is loosely associated in the literature with nonspecific “neuropathy” phenotypes, which are then connected to LHON via a “neuropathy → manifestation of LHON” edge (PMID 22019873).
• Similar logic is applied to ACHE and postural tremor/movement disorder.

Weaknesses:
– These are two-hop disease–disease bridges based on very broad phenotype terms (“neuropathy”, “movement disorder”).  They do not speak to the primary retinal ganglion cell degeneration seen in LHON and offer no mechanistic rationale for corticosteroid benefit.
– No clinical or pre-clinical study indicates that Betamethasone improves visual outcome in LHON; on the contrary, steroids are routinely ineffective in mitochondrial optic neuropathies that are initially misdiagnosed as optic neuritis.

IL-1 cytokine paths
• Betamethasone “interacts with” rilonacept or infliximab; those biologics modulate IL-1A/IL-1B, and IL-1 genes are asserted to be “associated with LHON” on the basis of PMID 7979221.
• PMID 7979221 is, in reality, a 1994 immunohistochemical study of cytokines in HIV myopathy; it does not mention LHON, making this edge spurious.

Overall assessment

• Evidence quality: extremely low.  Nearly all links are indirect, multi-hop, and hinge on generic interaction edges or on phenotypes only tangentially related to LHON.  The single solid paper (PMID 15838728) implicates TP53 as a modifier gene but provides no therapeutic angle for Betamethasone.

• Plausibility: poor.  Betamethasone’s known pharmacology (glucocorticoid receptor agonism) does not address the mitochondrial complex-I dysfunction or reactive oxygen species overproduction that underlie LHON, and there is no animal or human evidence of efficacy.

• Clinical readiness: none.  No registered trials, case series, or even anecdotal reports support corticosteroid use in LHON, and prior clinical experience generally shows no visual gain from steroids in these patients.

In short, the graph offers speculative, computation-driven connections that do not translate into a credible therapeutic hypothesis.  Current practice should continue to focus on agents with direct mitochondrial mechanisms (e.g., idebenone, EPI-743) until substantive experimental data emerge for corticosteroids."""

#for char in s:
#    print(f"-{char}-")


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


def matcher_aux_old(s, re, s_idx, re_idx, s_len, re_len, match_report):
    done = False
    while not done:
        if re_idx >= re_len: # later add s_idx >= s_len
            break
        # cur_char = s[s_idx]
        cur_regex = re[re_idx]
        cur_regex_type = cur_regex[0]
        cur_regex_expr = cur_regex[1]
        match cur_regex_type:
            case 'literal':
                print(f"a literal: {cur_regex}")
                cur_char = s[s_idx]
                rep = {'expr': cur_regex, 'start_pos': s_idx, 'end_pos': s_idx}
                if cur_char == cur_regex_expr:
                    s_idx += 1
                    re_idx += 1
                    rep['success'] = True
                    match_report.append(rep)
                else:
                    rep['success'] = False
                    match_report.append(rep)
                    break
            case 'union':
                print(f"the union for ever: {cur_regex_expr}")
                saved_s_idx = s_idx
                reports = []
                found_match = False
                for r in cur_regex_expr:
                    print(r)                    
                    # Wrap each sub-re in a tuple because matcher_aux* always expects a list of re's, not a bare one
                    rep = []
                    matcher_aux_old(s, (r, ), saved_s_idx, 0, s_len, 1, rep)
                    found_match = found_match or rep[-1]['success']
                    reports.append(rep)
                if found_match:
                    s_idx = 1 + max(x['end_pos'] for x in reports if x['success'])
                    re_idx += 1
                    match_report.append({'expr': cur_regex, 'start_pos': saved_s_idx, 'end_pos': s_idx-1, 'success': True})
                else:
                    match_report.append({'expr': cur_regex, 'start_pos': saved_s_idx, 'end_pos': -999, 'success': False})
                    break
            case 'star':                
                print(f"the big star: {cur_regex_expr}")
                report = []
                matcher_aux_old(s, cur_regex_expr, s_idx, 0, s_len, len(cur_regex_expr), report)
                re_idx += 1
            case _:
                print(f"HOW COULD THIS HAPPEN?? {cur_regex_type}")
                break
    print("done")

def matcher_aux_v2(s, re, s_idx, re_idx, s_len, re_len, match_report):
    print("top")
    # Note: order of tests matters
    if re_idx >= re_len:
        print("we are done!")
        return (True, s_idx, 2000)
    if s_idx >= s_len:
        return (False, s_idx, 3000)
    done = False
    saved_start_idx = s_idx
    while not done:
        print(f"in loop: re_idx: {re_idx}; re: {re}; re_len: {re_len}")        
        cur_regex = re[re_idx]
        cur_regex_type = cur_regex[0]
        cur_regex_expr = cur_regex[1]
        match cur_regex_type:
            case 'literal':
                print(f"a literal: {cur_regex}")
                cur_char = s[s_idx]
                rep = {'expr': cur_regex, 'start_pos': s_idx, 'end_pos': s_idx}
                if cur_char == cur_regex_expr:
                    s_idx += 1
                    re_idx += 1
                    rep['success'] = True
                    print(f"Literal match!")
                    match_report.append(rep)
                else:
                    rep['success'] = False
                    print(f"Literal FAIL match")
                    match_report.append(rep)
                    # break
                    return (False, s_idx, s_idx)
            case 'union':
                print(f"the union for ever: {cur_regex_expr}")
                saved_s_idx = s_idx
                reports = []
                found_any_match = False
                max_idx = 0
                for r in cur_regex_expr:
                    print(r)                    
                    # Wrap each sub-re in a tuple because matcher_aux* always expects a list of re's, not a bare one
                    rep = []
                    idx = saved_s_idx
                    found, orig_start_idx, final_idx = matcher_aux(s, (r, ), idx, 0, s_len, 1, rep)
                    found_any_match = found_any_match or found
                    max_idx = max([max_idx, idx])
                if found_any_match:
                    s_idx = 1 + max_idx
                    re_idx += 1
                    match_report.append({'expr': cur_regex, 'start_pos': saved_s_idx, 'end_pos': s_idx-1, 'success': True})
                else:
                    match_report.append({'expr': cur_regex, 'start_pos': saved_s_idx, 'end_pos': -999, 'success': False})
                    # break
                    return False
            case 'star':                
                print(f"the big star: {cur_regex_expr}")
                report = []
                saved_idx = s_idx
                found, orig_start_idx, final_idx = matcher_aux(s, cur_regex_expr, s_idx, 0, s_len, len(cur_regex_expr), report)
                if found:
                    s_idx = 1 + final_idx
                    print(f"Star match: {s[saved_idx:final_idx+1]}")
                    # do not increment re_idx; try to match again
                else:
                    # not matching star is not failure; restore s_idx and keep going
                    print(f"Star FAIL match: {s[saved_idx:final_idx+1]}")
                    s_idx = saved_idx
                    re_idx += 1
            case _:
                print(f"HOW COULD THIS HAPPEN?? {cur_regex_type}")
                break
        done = s_idx >= s_len or re_idx >= re_len
    print("done")
    if re_idx == re_len:
        return (True, saved_start_idx, s_idx)
    else:
        return (False, saved_start_idx, s_idx)

def matcher_aux(s, re, s_idx, re_idx, s_len, re_len, mr):
    saved_s_idx = s_idx
    while re_idx < re_len:
        cur_re = re[re_idx]
        cur_re_type = cur_re[0]
        cur_re_expr = cur_re[1]
        match cur_re_type:
            case 'literal':
                if s_idx >= s_len:
                    return (False, s_idx, s_idx)
                cur_char = s[s_idx]
                if cur_char == cur_re_expr:
                    s_idx += 1
                    re_idx += 1
                else:
                    return (False, s_idx, s_idx)
            case 'union':
                print("begin union match")
                found_any = False
                max_end_idx = 0
                for subexpr in cur_re_expr:
                    found, start, end = matcher_aux(s, subexpr, saved_s_idx, 0, s_len, len(subexpr), mr)
                    if found:
                        max_end_idx = max([max_end_idx, end])
                    found_any = found_any or found
                if found_any:
                    s_idx = max_end_idx + 1
                    re_idx += 1
                else:
                    return (False, saved_s_idx, max_end_idx)                
            case _:
                print("Whoops NYI")
                return (False, 999, 999)
    return (True, saved_s_idx, s_idx - 1)
                
    
def matcher(s, re):
    match_report = []
    retval, start_idx, end_idx = matcher_aux(s, re, 0, 0, len(s), len(re), match_report)
    print(f"Result: {retval}; {start_idx} - {end_idx}")

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
            (('literal', 'd'), ('literal', 'f'), ('literal', 'g'), ('literal', 'g'))
        ) 
        ), )
matcher('dfgagg', re8)

# Note cur behaviour is that trailing input is ignored once a match is found
print("end")
