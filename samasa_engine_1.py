#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Samasa engine: shared Sandhi first, then conservative Samasa analysis."""
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import sandhi_engine

def norm(s): return re.sub(r"\s+","",str(s or "")).lower()

def parse_verses(path: str | Path) -> list[dict[str, Any]]:
    """Parse GRETIL sa_rAmAyaNa.txt after the '# Text' marker.

    A śloka normally occupies two physical lines; the source reference
    R_kanda,sarga.verse occurs at the end of the second line. Both lines are
    joined into one verse record.
    """
    text = Path(path).read_text(encoding='utf-8')
    marker = re.search(r'(?im)^\s*#\s*Text\s*$', text)
    if marker:
        text = text[marker.end():]
    else:
        raise ValueError("Input file does not contain the '# Text' marker.")

    ref_re = re.compile(r'(?P<ref>R_(\d+),(\d+)\.(\d+))\s*$')
    verses=[]
    pending=[]
    for raw in text.splitlines():
        line=raw.strip()
        if not line or line.startswith('#'):
            continue
        m=ref_re.search(line)
        if m:
            body=line[:m.start()].strip()
            if body:
                pending.append(body)
            ref=m.group('ref')
            rm=re.match(r'R_(\d+),(\d+)\.(\d+)$',ref)
            if not rm:
                continue
            kanda,sarga,source_verse=map(int,rm.groups())
            verse_text=' '.join(pending).strip()
            pending=[]
            if verse_text:
                verses.append({'verse':len(verses)+1,'source_verse':source_verse,
                               'reference':ref,'kanda':kanda,'sarga':sarga,
                               'text':verse_text})
        else:
            pending.append(line)
    return verses


class SamasaEngine:
    def __init__(self,rulebook_path='samasah_rulebook.json'):
        self.rulebook_path=Path(rulebook_path); self.rb=json.loads(self.rulebook_path.read_text(encoding='utf-8'))
        self.rules=[]; self.by_compound={}; self.heads=set()
        for section in ('tatpurusha','bahuvrihi','dvandva','avyayibhava'):
            for rule in self.rb.get(section,[]):
                self.rules.append((section,rule))
                for ex in rule.get('examples',[]):
                    raw=str(ex.get('sandhi',''))
                    if '=' not in raw: continue
                    vig,comp=[x.strip() for x in raw.split('=',1)]
                    item={'rule_id':rule.get('id'),'samasa_class':section,'sanskrit_name':rule.get('sanskrit_name',''),'iast_name':rule.get('iast_name',''),'vigraha':vig,'compound':comp,'iast':ex.get('iast',''),'gloss':ex.get('gloss',''),'ashtadhyayi_ref':rule.get('ashtadhyayi_ref',''),'book_ref':rule.get('book_ref',''),'process':rule.get('process',''),'flagged_nuance':rule.get('flagged_nuance',''),'rule':rule.get('rule','')}
                    self.by_compound.setdefault(norm(comp),[]).append(item)
                    try: ci=sandhi_engine.devanagari_to_iast(comp)
                    except Exception: ci=''
                    self._heads(ci); self._heads(ex.get('iast',''))
    def _heads(self,s):
        # Extract only the right-hand side of known examples and retain distinctive suffixes.
        w=norm(s.split('=')[-1])
        for n in (5,6,7,8,9):
            if len(w)>n: self.heads.add(w[-n:])
        # Conservative compound-head lexicon used only to propose a split.
        # It does not assign a Samasa class by itself.
        for h in ('puṃgava','jña','jñā','vrata','darśana','bāhu','grīva','hanu','vīrya','guṇa','upeta','sampanna','prabhava','vardhana','indriya','ātman'):
            self.heads.add(h)
    def exact(self,t): return self.by_compound.get(norm(t),[])
    def candidate(self,t):
        w=norm(t)
        if len(w)<7: return False
        # Surface forms may carry case/number endings (e.g. puṃgavam) or
        # final Sandhi consonants (e.g. jñaś).  Test the lexical member before
        # these endings, but never alter the original token.
        for h in self.heads:
            if w.endswith(h) and len(w)>len(h)+1: return True
            for ending in ('am','m','aḥ','ḥ','as','s','aṃ','ṃ','an','n','ar','r','a','i','ī','u','ū','o','e','ś'):
                if w.endswith(h+ending) and len(w)>len(h+ending)+1: return True
        return False
    def split_candidate(self,t):
        w=norm(t)
        explicit=("puṃgava","jña","jñā","vrata","darśana","bāhu","grīva","hanu","vīrya","guṇa","upeta","sampanna","prabhava","vardhana","indriya","ātman")
        ordered=list(explicit)+[h for h in sorted(self.heads,key=len,reverse=True) if h not in explicit]
        endings=("am","m","aḥ","ḥ","as","s","aṃ","ṃ","an","n","ar","r","a","i","ī","u","ū","o","e","ś")
        for h in ordered:
            if w.endswith(h) and len(w)>len(h)+1:
                return {"पूर्वांशः":w[:-len(h)],"उत्तरांशः":h,"विग्रहविच्छेदः":w[:-len(h)]+" + "+h}
            for ending in endings:
                surf=h+ending
                if w.endswith(surf) and len(w)>len(surf)+1:
                    return {"पूर्वांशः":w[:-len(surf)],"उत्तरांशः":surf,"मूलोत्तरपदम्":h,"रूपान्तः":ending,"विग्रहविच्छेदः":w[:-len(surf)]+" + "+surf}
        return None

    def analyse(self,t,deva,pos):
        hits=self.exact(t)
        if hits:
            return {'क्रमः':pos,'token_IAST':t,'token_देवनागरी':deva,'candidate':True,'स्थितिः':'निश्चितम्','प्रस्ताविताः':hits}
        if self.candidate(t):
            sp=self.split_candidate(t)
            return {'क्रमः':pos,'token_IAST':t,'token_देवनागरी':deva,'candidate':True,'स्थितिः':'सम्भावितम्','प्रस्ताविताः':[],'संभावित_विभाजनानि':[sp] if sp else [],'candidate_note':'Rulebook-derived compound pattern; member split is a candidate only. विग्रहः/समासभेदः is not guessed.'}
        return None
    def process_verse(self,v,se,ctx):
        text=v['text']; deva=sandhi_engine.iast_to_devanagari(text); toks=text.split(); dt=deva.split(); comps=[]
        for i,(t,d) in enumerate(zip(toks,dt),1):
            a=self.analyse(t,d,i)
            if a: comps.append(a)
        boundaries=[]
        for i in range(len(dt)-1):
            cand=se.explain(dt[i],dt[i+1],ctx)
            boundaries.append({'क्रमः':i+1,'पूर्वपदम्_IAST':sandhi_engine.devanagari_to_iast(dt[i]),'उत्तरपदम्_IAST':sandhi_engine.devanagari_to_iast(dt[i+1]),'पूर्वपदम्':dt[i],'उत्तरपदम्':dt[i+1],'सन्धि_प्रस्तावाः':[dict(x,**{'परिणामः_IAST':sandhi_engine.devanagari_to_iast(x['परिणामः'])}) for x in cand]})
        return {'verse':v['verse'],'source_verse':v['source_verse'],'reference':v['reference'],'kanda':v['kanda'],'sarga':v['sarga'],'original_IAST':text,'devanagari_internal':deva,'token_count':len(toks),'sandhi_boundaries':boundaries,'identified_compounds':comps}
    def process_file(self,input_path,start,end,sandhi_rulebook):
        verses=parse_verses(input_path); sel=[v for v in verses if start<=v['verse']<=end]; se=sandhi_engine.SandhiEngine(sandhi_rulebook)
        return {'engine':'samasa_engine','pipeline':'sandhi_engine -> token analysis -> samasa_engine','rulebook':str(self.rulebook_path),'sandhi_rulebook':str(sandhi_rulebook),'source':str(input_path),'encoding':'UTF-8','input_script':'IAST','start_verse':start,'end_verse':end,'verses_found':len(verses),'verses_processed':len(sel),'rulebook_summary':self.rb.get('summary_counts',{}),'results':[self.process_verse(v,se,{}) for v in sel]}
    def report(self):
        return {'engine':'samasa_engine','rulebook':str(self.rulebook_path),'samasa_rule_entries':len(self.rules),'worked_examples_indexed':sum(map(len,self.by_compound.values())),'classes':{s:sum(1 for x,_ in self.rules if x==s) for s in ('tatpurusha','bahuvrihi','dvandva','avyayibhava')},'candidate_head_patterns':len(self.heads)}

DEFAULT_SANDHI_RULEBOOK = str(HERE.parent / 'sandhi' / 'sandhi_rulebook.json')

def main():
    p=argparse.ArgumentParser(); p.add_argument('--rulebook',default=str(HERE / 'samasah_rulebook.json')); p.add_argument('--sandhi-rulebook',default=DEFAULT_SANDHI_RULEBOOK); p.add_argument('--compile-report',action='store_true'); p.add_argument('--input'); p.add_argument('--start-verse',type=int); p.add_argument('--end-verse',type=int); p.add_argument('--output'); p.add_argument('--format',choices=('json','txt'),default='json'); p.add_argument('--compound'); a=p.parse_args(); e=SamasaEngine(a.rulebook)
    if a.compile_report: print(json.dumps(e.report(),ensure_ascii=False,indent=2))
    if a.compound:
        t=a.compound; ti=sandhi_engine.devanagari_to_iast(t) if re.search('[\u0900-\u097f]',t) else t; print(json.dumps(e.analyse(ti,sandhi_engine.iast_to_devanagari(ti),1),ensure_ascii=False,indent=2))
    if a.input:
        if None in (a.start_verse,a.end_verse) or not a.output: p.error('--input requires --start-verse, --end-verse and --output')
        d=e.process_file(a.input,a.start_verse,a.end_verse,a.sandhi_rulebook); o=Path(a.output); o=o.with_suffix('.json' if a.format=='json' else '.txt');
        if a.format=='json': o.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
        else:
            lines=[f"Samasa Engine validation output\nSource: {d['source']}\nVerses: {a.start_verse} - {a.end_verse}\n"]
            for v in d['results']:
                lines.append(f"Verse {v['verse']} [{v['reference']}]: {v['original_IAST']}")
                for c in v['identified_compounds']:
                    lines.append(f"  {c['token_IAST']} -> {c['token_देवनागरी']} [{c['स्थितिः']}]")
                    for h in c['प्रस्ताविताः']: lines.append(f"    {h['samasa_class']} | {h['sanskrit_name']} | {h['rule_id']} | {h['vigraha']} = {h['compound']}")
            o.write_text('\n'.join(lines),encoding='utf-8')
        print(f'Wrote {o} ({d["verses_processed"]} verses)')
    if not (a.compile_report or a.compound or a.input): p.print_help()
if __name__=='__main__': main()
