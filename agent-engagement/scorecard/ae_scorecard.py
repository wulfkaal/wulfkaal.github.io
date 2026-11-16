#!/usr/bin/env python3
"""Separate access and discovery diagnostics, with an anonymous cohort."""
import argparse
import collections
import datetime
import hashlib
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import uuid
import random
import math

VERSION = '0.1'
_SECRETS = set()
ROOT = Path(__file__).resolve().parents[1]
UA = 'AEScorecard/0.1 (+https://wulfkaal.com/agent-engagement/scorecard/; diagnostic request, not a crawler; contact via the site)'
TOKENS = 'GPTBot ChatGPT-User OAI-SearchBot ClaudeBot Claude-User Claude-SearchBot anthropic-ai PerplexityBot Perplexity-User Google-Extended CCBot Applebot-Extended Bytespider meta-externalagent Googlebot'.split()
METRICS = ['works', 'cited_by', 'h_index', 'oa_works', 'oa_recent', 'oa_share_grouped', 'oa_share_profile']
SCOPE = 'Access and discoverability diagnostics. The scorecard is not AE. No composite number or global ranking is produced. Unobserved engagement is missing, not zero.'
DISCLOSURE = 'Designer-operated and self-reported. Wulf A. Kaal designed the AE proposal, appears in the 2024 Sisk-Leiter list, and is a colleague of its principal author. This exploratory project has a single operator and no independent co-maintainer yet.'
LIMITS = "The cohort comprises each school's ten most-cited faculty who resolved in OpenAlex. Field, career stage, language and publication-type effects are not adjusted. OpenAlex coverage of law is incomplete. Name matching errors exist."
CLASSIFIER = 'No agent-traffic classifier is used in v0.1. Validation would require labeled samples, provider verification, false positive and false negative estimates, and an unknown category.'
DEFINITIONS = {'works': 'OpenAlex profile works_count', 'cited_by': 'OpenAlex profile cited_by_count', 'h_index': 'OpenAlex summary_stats.h_index', 'oa_works': 'Grouped is_oa:true count', 'oa_recent': 'OA works published after 2021', 'oa_share_grouped': 'oa/(oa+nonoa); missing when denominator is zero', 'oa_share_profile': 'oa/works; missing when denominator is zero'}

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def redact(value):
    if isinstance(value, dict):
        return {k: ('REDACTED' if k.lower() == 'api_key' else redact(v)) for k, v in value.items()}
    if isinstance(value, list): return [redact(v) for v in value]
    if isinstance(value, str):
        for secret in _SECRETS:
            value = value.replace(secret, 'REDACTED').replace(urllib.parse.quote(secret, safe=''), 'REDACTED').replace(urllib.parse.quote_plus(secret), 'REDACTED')
        return re.sub(r'(?i)(api_key(?:=|%3D))[^&\s\"<>]+', r'\1REDACTED', value)
    return value

def obj(value):
    return value if isinstance(value, dict) else {}

def index_summary(kind, data):
    d = obj(data)
    if kind == 'orcid':
        activities = obj(d.get('activities-summary'))
        return {'resolved': bool(d.get('orcid-identifier')), 'work_group_count': len(obj(activities.get('works')).get('group') or []), 'last_modified_date': obj(obj(d.get('history')).get('last-modified-date')).get('value'), 'external_identifier_count': len(obj(obj(d.get('person')).get('external-identifiers')).get('external-identifier') or [])}
    if kind == 'openalex':
        result = {k: d.get(k) for k in ('display_name', 'works_count', 'cited_by_count', 'orcid')}
        result.update(id_suffix=str(d.get('id') or '').rsplit('/', 1)[-1], h_index=obj(d.get('summary_stats')).get('h_index'))
        for key in ('works_count','cited_by_count','h_index'):
            v=result.get(key)
            if type(v) is not int or v < 0: result[key]=None
        years = d.get('counts_by_year')
        if isinstance(years, list) and len(years) <= 20:
            result['counts_by_year'] = [{k: obj(y).get(k) for k in ('year', 'works_count', 'cited_by_count')} for y in years]
        return result
    return {'total_results': obj(d.get('message')).get('total-results')}

def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(redact(value), indent=2, ensure_ascii=True) + '\n')

def read(path):
    return json.loads(Path(path).read_text())

def shares(oa, nonoa, works):
    oa, nonoa, works = [v if type(v) in (int,float) and math.isfinite(v) and v >= 0 else None for v in (oa,nonoa,works)]
    a = oa / (oa + nonoa) if oa is not None and nonoa is not None and oa + nonoa else None
    b = oa / works if oa is not None and works else None
    return {'oa_share_grouped': a, 'oa_share_profile': b, 'oa_denominator_grouped': oa + nonoa if oa is not None and nonoa is not None else None, 'oa_denominator_profile': works, 'oa_share_discrepancy': a - b if a is not None and b is not None else None}

def quantile(values, q):
    if not values:
        return None
    v = sorted(values)
    x = (len(v) - 1) * q
    i = int(x)
    return v[i] + (v[min(i + 1, len(v) - 1)] - v[i]) * (x - i)

def position(value, values):
    n = len(values)
    rank = 1 + sum(x > value for x in values)
    ties = values.count(value)
    return {'position': rank, 'N': n, 'tie_size': ties, 'text': '{}position {} of {} (competition ranking; tie size {})'.format('joint ' if ties > 1 else '', rank, n, ties)}

def cohort(rows):
    resolved = [r for r in rows if r.get('resolved') and r.get('openalex_id')]
    counts = collections.Counter(r['openalex_id'] for r in resolved)
    duplicate = {k for k, n in counts.items() if n > 1}
    out = {'date': now(), 'method': 'resolved Sisk-Leiter-listed OpenAlex records (provisional)', 'definitions': DEFINITIONS, 'duplicate_profile_count': len(duplicate), 'exclusions': {'unresolved_records': len(rows) - len(resolved), 'shared_profile_records': sum(counts[k] for k in duplicate)}, 'quantile_rule': 'Linear interpolation at (N-1)*p on ascending values.'}
    for label, subset in [('primary', [r for r in resolved if r['openalex_id'] not in duplicate]), ('sensitivity', resolved)]:
        values = {m: [] for m in METRICS}
        for r in subset:
            metrics = dict(r)
            metrics.update(shares(r.get('oa_works'), r.get('nonoa_works'), r.get('works')))
            for m in METRICS:
                if type(metrics.get(m)) in (int, float) and math.isfinite(metrics[m]) and metrics[m] >= 0:
                    values[m].append(metrics[m])
        out[label] = {'N': len(subset), 'values': {m: sorted(v) for m, v in values.items()}, 'metric_N': {m: len(v) for m, v in values.items()}}
    qs = {k: v for k, v in out.items() if k not in ('primary', 'sensitivity')}
    for label in ('primary', 'sensitivity'):
        qs[label] = {'N': out[label]['N'], 'metric_N': out[label]['metric_N'], 'quantiles': {m: {name: quantile(v, p) for name, p in [('min', 0), ('p10', .1), ('p25', .25), ('median', .5), ('p75', .75), ('p90', .9), ('max', 1)]} for m, v in out[label]['values'].items()}}
    return out, qs

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.title = ''
        self.meta = {}
        self.links = []
        self.lang = None
        self.blocks = []
        self.in_title = False
        self.ld = None
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html': self.lang = a.get('lang')
        if tag == 'title': self.in_title = True
        if tag == 'meta': self.meta[a.get('name', a.get('property', ''))] = a.get('content', '')
        if tag in ('a', 'link'): self.links.append(a)
        if tag == 'script' and a.get('type') == 'application/ld+json': self.ld = ''
    def handle_data(self, data):
        if self.in_title: self.title += data
        if self.ld is not None: self.ld += data
    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False
        if tag == 'script' and self.ld is not None:
            try: self.blocks.append({'valid': True, 'data': json.loads(self.ld)})
            except ValueError: self.blocks.append({'valid': False})
            self.ld = None

def types(value):
    found = []
    if isinstance(value, dict):
        t = value.get('@type', [])
        found.extend(t if isinstance(t, list) else [t])
        for v in value.values(): found.extend(types(v))
    elif isinstance(value, list):
        for v in value: found.extend(types(v))
    return sorted(set(found))

def body_check(body, status, content_type):
    s = body.decode('utf-8', 'replace').lower()
    if not body.strip(): return 'empty_body'
    if any(x in s for x in ('verify you are human', 'cf-chl-', 'captcha', 'just a moment')): return 'challenge_page'
    if status and status >= 400: return 'error_page'
    if 'html' not in content_type.lower(): return 'non_html'
    if Page(s).title.strip(): return 'ok_html_with_title'
    return 'unknown'

def checklist(body, page_type="article", content_type="text/html", machine_format=None):
    if page_type == "machine_file":
        is_json = machine_format == "json" or (machine_format is None and "json" in content_type)
        try:
            if is_json: json.loads(body)
            else: body.decode("utf-8", "strict")
            parses = True
        except (ValueError, UnicodeError): parses = False
        return {"page_type": page_type, "items": {"parses": "pass" if parses else "fail", "content_type": "pass" if ("json" in content_type if is_json else "text/plain" in content_type) else "fail", "size": "pass" if 0 < len(body) <= 150000 else "fail"}}
    p = Page(body.decode('utf-8', 'replace'))
    ts = types([b.get('data') for b in p.blocks])
    checks = {'title': bool(p.title.strip()), 'description': bool(p.meta.get('description')), 'canonical': any('canonical' in a.get('rel', '') for a in p.links), 'lang': bool(p.lang), 'open_graph': any(k.startswith('og:') for k in p.meta), 'highwire': bool(p.meta.get('citation_title')) and any(p.meta.get(k) for k in ('citation_author', 'citation_publication_date', 'citation_pdf_url', 'citation_doi')), 'json_ld': bool(p.blocks) and all(b['valid'] for b in p.blocks), 'doi_links': any('doi.org/' in a.get('href', '') for a in p.links), 'license': any('license' in a.get('rel', '') for a in p.links)}
    checks.update({t: t in ts for t in ['Dataset', 'ScholarlyArticle', 'Person', 'SoftwareSourceCode']})
    return {'page_type': page_type, 'items': {k: ('not_applicable' if k == 'highwire' and page_type != 'article' else 'pass' if v else 'fail') for k, v in checks.items()}, 'title': p.title, 'json_ld': [{'valid': b['valid']} for b in p.blocks], 'types': ts}

def robots(text, urls):
    p = urllib.robotparser.RobotFileParser()
    p.parse(text.splitlines())
    root = urllib.parse.urljoin(urls[0], '/') if urls else '/'
    baseline = {t: p.can_fetch(t, root) for t in TOKENS}
    return {'state': 'published_rules', 'root_url': root, 'root_rules': baseline, 'path_differences': {u: diff for u in urls if (diff := {t: p.can_fetch(t, u) for t in TOKENS if p.can_fetch(t, u) != baseline[t]})}, 'content_signal_lines': [s for s in text.splitlines() if s.strip().lower().startswith('content-signal:')]}

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None

class Client:
    def __init__(self, output):
        self.output = Path(output)
        self.run_id = self.output.name if self.output.parent.name == 'runs' else str(uuid.uuid4())
        self.start = now()
        self.log = []
        self.last = 0
        self.opener = urllib.request.build_opener(NoRedirect())
    def fetch(self, url, accept=None):
        chain = []
        headers = {'User-Agent': UA}
        if accept: headers['Accept'] = accept
        if urllib.parse.urlsplit(url).hostname == 'api.openalex.org':
            key = os.environ.get('OPENALEX_API_KEY')
            if key:
                _SECRETS.add(key)
                url += ('&' if '?' in url else '?') + urllib.parse.urlencode({'api_key': key})
        original = redact(url)
        body = b''
        for hop in range(6):
            body = b''
            if urllib.parse.urlsplit(url).scheme not in ('http', 'https'):
                record = {'run_id':self.run_id,'utc':now(),'request_headers':headers.copy(),'url':redact(url),'status':None,'error_type':'InvalidScheme','body_check':'unknown','content_type':'','byte_count':0,'body_sha256':hashlib.sha256(b'').hexdigest()}
                chain.append(record); self.log.append(record); self.flush(); break
            time.sleep(max(0, 1 - (time.monotonic() - self.last)))
            self.last = time.monotonic()
            record = {'run_id': self.run_id, 'url': redact(url), 'utc': now(), 'request_headers': headers.copy(), 'status': None, 'error_type': None, 'content_type': '', 'byte_count': 0, 'body_sha256': hashlib.sha256(b'').hexdigest(), 'body_check': 'unknown'}
            try:
                try: response = self.opener.open(urllib.request.Request(url, headers=headers), timeout=20)
                except urllib.error.HTTPError as e: response = e
                with response:
                    record.update(status=response.code, content_type=response.headers.get('Content-Type', ''))
                    location = response.headers.get('Location')
                    record['location'] = redact(urllib.parse.urljoin(url, location)) if location else None
                    body = response.read(32000001)
                record.update(byte_count=len(body), body_sha256=hashlib.sha256(body).hexdigest(), body_check=body_check(body, record['status'], record['content_type']))
            except Exception as e:
                record['error_type'] = type(e).__name__
                record['observation'] = ('body read error: {}' if record['status'] is not None else 'no HTTP response (client error: {})').format(type(e).__name__)
                record['body_read_error'] = record['status'] is not None
                location = None
            if len(body) > 32000000:
                body = body[:32000000]
                record.update(body_check='truncated', error_type='OversizeBody', byte_count=len(body), body_sha256=hashlib.sha256(body).hexdigest())
            chain.append(record)
            self.log.append(record)
            self.flush()
            if record['status'] not in (301, 302, 303, 307, 308) or not location: break
            if hop == 5:
                record['error_type'] = 'RedirectLimit'
                self.flush()
                break
            url = urllib.parse.urljoin(url, location)
        return {**chain[-1], 'url': original, 'redirect_chain': chain}, body
    def flush(self):
        save(self.output / 'request_log.json', self.log)
        save(self.output / 'exclusion_register.json', {'test_run_id': self.run_id, 'utc_start': self.start, 'utc_end': now(), 'user_agent': UA, 'urls': [r['url'] for r in self.log]})

def api(client, url, accept='application/json'):
    observation, body = client.fetch(url, accept)
    try: data = json.loads(body)
    except ValueError: data = None
    valid = valid_payload(url, data)
    return {'observation': observation, 'data': data if valid else None, 'state': 'observed' if valid and observation['status'] == 200 and not observation.get('error_type') else 'unknown'}

def matching(url, config):
    p = urllib.parse.urlsplit(url)
    if p.scheme not in ('http', 'https') or p.username or p.password: return False
    host = (p.hostname or '').lower()
    if host in ('wulfkaal.com', 'wulfkaal.github.io'): return True
    if url.rstrip('/') in [u.rstrip('/') for u in config.get('owner_profile_urls', [])]: return True
    if host == 'papers.ssrn.com' and p.path.lower() == '/sol3/cf_dev/absbyauth.cfm':
        return urllib.parse.parse_qs(p.query).get('per_id') == [str(config['ssrn_author_id'])]
    if host == 'orcid.org': return p.path.strip('/') == config['orcid'] and not p.query
    if host == 'openalex.org': return p.path.strip('/') in (config['openalex_author_id'], 'authors/' + config['openalex_author_id']) and not p.query
    if host in ('doi.org', 'dx.doi.org') and not p.query:
        doi = urllib.parse.unquote(p.path.lstrip('/')).lower()
        return bool(re.fullmatch(r'10\.\d{4,9}/\S+', doi)) and doi in [d.lower() for d in config.get('dois', [])]
    return False

def import_retrieval(data, config):
    if not isinstance(data, dict): raise ValueError('Expected object')
    for key in ('agent', 'date', 'locale', 'cutoff', 'queries'):
        if key not in data: raise ValueError('Missing retrieval field: ' + key)
    if not isinstance(data['agent'], dict) or any(not isinstance(data['agent'].get(k), str) or not data['agent'][k].strip() for k in ('name','model','tool')): raise ValueError('Invalid agent')
    datetime.date.fromisoformat(data['date'])
    if not isinstance(data['locale'], str) or not data['locale']: raise ValueError('Invalid locale')
    if type(data['cutoff']) is not int or data['cutoff'] < 1: raise ValueError('Invalid cutoff')
    if not isinstance(data['queries'], list): raise ValueError('Invalid queries')
    for q in data['queries']:
        if not isinstance(q, dict) or not isinstance(q.get('q'), str) or not q['q'] or not isinstance(q.get('results'), list): raise ValueError('Invalid query')
        seen = set()
        for r in q['results']:
            if not isinstance(r, dict) or type(r.get('rank')) is not int or r['rank'] < 1 or r['rank'] in seen: raise ValueError('Invalid or duplicate rank')
            seen.add(r['rank'])
            u = urllib.parse.urlsplit(r.get('url', ''))
            if u.scheme not in ('http','https') or not u.hostname or u.username or u.password: raise ValueError('Invalid URL')
    return {**data, 'queries': [{**q, 'found': any(matching(r['url'], config) for r in q['results'] if r['rank'] <= data['cutoff']), 'matching_ranks': [r['rank'] for r in q['results'] if r['rank'] <= data['cutoff'] and matching(r['url'], config)]} for q in data['queries']], 'interpretation': 'Per-query demonstrations only.'}

def profile_metrics(client, author):
    base = 'https://api.openalex.org/'
    p = api(client, base + 'authors/' + urllib.parse.quote(author, safe=''))
    if p['state'] == 'unknown': return {'state': 'unknown', 'error': p['observation']}
    a = obj(p['data'])
    metrics = {'works': a.get('works_count'), 'cited_by': a.get('cited_by_count'), 'h_index': obj(a.get('summary_stats')).get('h_index')}
    grouped = api(client, base + 'works?' + urllib.parse.urlencode({'filter': 'author.id:' + str(a.get('id') or author), 'group_by': 'open_access.is_oa', 'per-page': 200}))
    recent = api(client, base + 'works?' + urllib.parse.urlencode({'filter': 'author.id:' + str(a.get('id') or author) + ',open_access.is_oa:true,from_publication_date:2022-01-01', 'per-page': 1}))
    if grouped['state'] == 'observed':
        groups = {str(g['key']).lower(): g['count'] for g in grouped['data'].get('group_by', []) if isinstance(g, dict) and type(g.get('count')) is int and g['count'] >= 0}
        oa, nonoa = groups.get('true'), groups.get('false')
        metrics.update(oa_works=oa, nonoa_works=nonoa)
        metrics.update(shares(oa, nonoa, metrics['works']))
    metrics['oa_recent'] = obj(obj(recent['data']).get('meta')).get('count') if recent['state'] == 'observed' else None
    metrics = {k: v if type(v) in (int,float) and math.isfinite(v) and v >= 0 else None for k,v in metrics.items()}
    return {'state': 'observed' if all(metrics.get(m) is not None for m in METRICS) else 'partial', 'metrics': metrics}

def run_module(name, args, config, client):
    out = Path(args.output)
    if name == 'access':
        pages = [client.fetch(u)[0] for u in config['canonical_urls']]
        hosts = sorted({urllib.parse.urlsplit(u).scheme + '://' + urllib.parse.urlsplit(u).netloc for u in config['canonical_urls'] if 'papers.ssrn.com' not in u})
        policies = []
        for host in hosts:
            targets = [u for u in config['canonical_urls'] if u.startswith(host + '/')]
            r, b = client.fetch(host + '/robots.txt')
            policy = robots(b.decode('utf-8', 'replace'), targets) if r['status'] == 200 else {'state': 'no_restrictions_published' if r['status'] in (404, 410) else 'unknown', 'http_status': r['status'], 'interpretation': 'Missing robots.txt publishes no restrictions; it is not observed permission.' if r['status'] in (404, 410) else 'Robots policy could not be observed.'}
            policy['http_status'] = r['status']
            s, sb = client.fetch(host + '/sitemap.xml')
            l, lb = client.fetch(host + '/llms.txt')
            policies.append({'host': host, 'robots': policy, 'sitemap': {u: (html.escape(u).encode() in sb or u.encode() in sb) if s['status'] == 200 else 'unknown' for u in targets}, 'llms_exists': l['status'] == 200 if l['status'] else 'unknown', 'llms_links': {u: u.encode() in lb if l['status'] == 200 else 'unknown' for u in targets}})
        result = {'pages': pages, 'policies': policies}
    elif name == 'readability':
        result = {}
        for u in config['canonical_urls']:
            if 'papers.ssrn.com' in u:
                result[u] = {'state': 'unknown', 'reason': 'Single observation is reserved for access.'}
                continue
            r, b = client.fetch(u)
            result[u] = checklist(b, config.get('page_types', {}).get(u, 'article'), r['content_type'], 'json' if u.endswith(('.json', '.jsonld')) else 'text') if r['status'] == 200 else {'state': 'unknown'}
            result[u]['observation'] = r
    elif name == 'indexes':
        identifier = config['openalex_author_id'] or 'https://orcid.org/' + config['orcid']
        result = {'openalex': api(client, 'https://api.openalex.org/authors/' + urllib.parse.quote(identifier, safe='')), 'orcid': api(client, 'https://pub.orcid.org/v3.0/' + config['orcid'] + '/record'), 'crossref': api(client, 'https://api.crossref.org/works?' + urllib.parse.urlencode({'filter': 'orcid:https://orcid.org/' + config['orcid'], 'rows': 0})), 'semantic_scholar': {'state': 'not queried (optional)'}, 'google_scholar': 'not queried (no sanctioned API for automated access)', 'ssrn': 'not queried (no sanctioned API for automated access)'}
        for kind in ('openalex', 'orcid', 'crossref'):
            result[kind]['data'] = index_summary(kind, result[kind]['data'])
    elif name == 'retrieval':
        if getattr(args, 'import_file', None): result = import_retrieval(read(args.import_file), config)
        elif getattr(args, 'openalex', False) or args.command == 'all':
            observations = []
            for q in config['topic_queries']:
                try:
                    o = api(client, 'https://api.openalex.org/works?' + urllib.parse.urlencode({'search': q, 'per-page': 25}))
                    c = api(client, 'https://api.crossref.org/works?' + urllib.parse.urlencode({'query.bibliographic': q, 'rows': 25}))
                    works = obj(o['data']).get('results') or []
                    cr = obj(obj(c['data']).get('message')).get('items') or []
                    ranks = [i for i, w in enumerate(works, 1) if any(str(obj(obj(a).get('author')).get('id') or '').endswith('/' + config['openalex_author_id']) for a in obj(w).get('authorships') or [])]
                    cross = [i for i, w in enumerate(cr, 1) if str(obj(w).get('DOI') or '').lower() in [d.lower() for d in config['dois']]]
                    observations.append({'q': q, 'date': now(), 'locale': 'API default', 'cutoff': 25, 'tool_model': 'OpenAlex works search and Crossref query.bibliographic; no model', 'openalex': {'state': o['state'], 'found': bool(ranks) if o['state'] == 'observed' else 'unknown', 'matching_ranks': ranks, 'results': [{'rank': i, 'url': obj(w).get('id')} for i, w in enumerate(works, 1)]}, 'crossref': {'state': c['state'], 'found': bool(cross) if c['state'] == 'observed' and config['dois'] else 'unknown', 'matching_ranks': cross, 'results': [{'rank': i, 'url': obj(w).get('URL')} for i, w in enumerate(cr, 1)]}})
                    if o['state'] == 'unknown' or c['state'] == 'unknown':
                        failed = o if o['state'] == 'unknown' else c
                        obs = failed.get('observation', {})
                        observations[-1].update(state='unknown', error=obs.get('error_type') or ('HTTPError' if obs.get('status') != 200 else 'InvalidPayload'))
                except Exception as e:
                    observations.append({'q': q, 'date': now(), 'state': 'unknown', 'error': type(e).__name__})
            result = {'queries': observations, 'interpretation': 'Per-query demonstrations only.'}
        else: result = {'state': 'unknown', 'reason': 'Select --openalex or --import.'}
    elif name == 'compare':
        try:
            result = profile_metrics(client, getattr(args, 'author', None) or config['openalex_author_id'])
            if result['state'] in ('observed', 'partial'):
                cohort_path = Path(getattr(args, 'cohort', None) or ROOT / 'results/cohort_exact.json')
                if not cohort_path.exists():
                    values, qs = cohort(read(ROOT.parent / 'data/scholars_openalex.json'))
                    cohort_path=out/'cohort_exact.json'
                    save(cohort_path, values)
                    save(cohort_path.with_name('cohort_quantiles.json'), qs)
                values = read(cohort_path)
                result['comparison'] = {label: {'N': values[label]['N'], 'positions': {m: (position(v, values[label]['values'][m]) if not getattr(args, 'author', None) or args.author == config['openalex_author_id'] else insertion_position(v, values[label]['values'][m])) for m, v in result['metrics'].items() if m in METRICS and v is not None}} for label in ('primary', 'sensitivity')}
                result['method'] = 'provisional comparison within the resolved Sisk-Leiter-listed cohort'
                result['benchmark']={'path':str(cohort_path),'sha256':hashlib.sha256(cohort_path.read_bytes()).hexdigest(),'date':values.get('date'),'protected':bool(values.get('privacy'))}
        except Exception as e:
            result = {'state': 'unknown', 'error': type(e).__name__, 'reason': 'Comparison could not be completed.'}
    else: raise ValueError(name)
    result['run_id'] = client.run_id if hasattr(client, 'run_id') else 'fixture'
    save(out / (name + '.json'), result)
    return result

def document(title, content, filename, kind='TechArticle'):
    url = 'https://wulfkaal.com/agent-engagement/scorecard/' + ('' if filename == 'index.html' else filename)
    return '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + html.escape(title) + '</title><meta name="description" content="Access and discoverability diagnostics for scholarly records"><link rel="canonical" href="' + url + '"><meta property="og:title" content="' + html.escape(title) + '"><meta property="og:type" content="article"><meta property="og:url" content="' + url + '"><meta property="og:description" content="Provisional scholarly diagnostics"><meta name="citation_title" content="' + html.escape(title) + '"><meta name="citation_author" content="Wulf A. Kaal"><meta name="citation_publication_date" content="2026/11/15"><script type="application/ld+json">' + json.dumps({'@context': 'https://schema.org', '@type': kind, 'name': title, 'url': url, 'author': {'@type': 'Person', 'name': 'Wulf A. Kaal'}}) + '</script><style>body{font-family:system-ui,sans-serif;max-width:76rem;margin:auto;padding:1rem;line-height:1.5}table{border-collapse:collapse;width:100%;margin:1rem 0}th,td{border:1px solid #aaa;padding:.4rem;text-align:left;overflow-wrap:anywhere}nav ul{padding-left:1.5rem}svg{max-width:100%}</style></head><body><header><a href="index.html">Scorecard</a></header><main><h1>' + html.escape(title) + '</h1>' + content + '</main></body></html>\n'

def valid_payload(url, data):
    if not isinstance(data, dict): return False
    p = urllib.parse.urlsplit(url)
    if p.hostname == 'api.openalex.org':
        if '/authors/' in p.path:
            return isinstance(data.get('id'), str) and all(type(data.get(k)) is int and data[k] >= 0 for k in ('works_count','cited_by_count'))
        query = urllib.parse.parse_qs(p.query)
        if 'group_by' in query:
            groups = data.get('group_by')
            return isinstance(groups, list) and all(isinstance(g,dict) and str(g.get('key')).lower() in ('true','false') and type(g.get('count')) is int and g['count'] >= 0 for g in groups)
        if 'search' in query:
            return isinstance(data.get('results'), list) and all(isinstance(w,dict) and isinstance(w.get('authorships'),list) and bool(w['authorships']) and all(isinstance(a,dict) and isinstance(a.get('author'),dict) and isinstance(a['author'].get('id'),str) and bool(re.fullmatch(r'https://openalex.org/A[0-9]+',a['author']['id'])) for a in w['authorships']) for w in data['results'])
        return (type(obj(data.get('meta')).get('count')) is int and data['meta']['count'] >= 0)
    if p.hostname == 'api.crossref.org':
        m = obj(data.get('message'))
        return isinstance(m.get('items'),list) if 'query.bibliographic' in p.query else (type(m.get('total-results')) is int and m['total-results'] >= 0)
    if p.hostname == 'pub.orcid.org': return isinstance(data.get('orcid-identifier'),dict) and isinstance(data.get('activities-summary'),dict)
    return True


def insertion_position(value, values):
    rank = 1 + sum(x > value for x in values)
    ties = 1 + values.count(value)
    return {'position': rank, 'N': len(values), 'tie_size': ties, 'semantics': 'Insertion against fixed benchmark; tie size includes principal; position may be N+1.', 'text': 'insertion position {} against {} benchmark records (tie size including principal {})'.format(rank,len(values),ties)}


def protect_cohort(values):
    import copy
    public = copy.deepcopy(values)
    public['privacy'] = 'Distributions without direct identifiers, not guaranteed anonymous. Bottom three replaced by fourth and top three by fourth from top when N >= 7. Shares rounded to 2 decimals. Exact local ranking benchmark is unchanged. Public ranks may differ, especially at extremes and rounded ties.'
    for label in ('primary','sensitivity'):
        for m,v in public[label]['values'].items():
            if len(v) >= 7: v[:3],v[-3:] = [v[3]]*3,[v[-4]]*3
            if m.startswith('oa_share'): public[label]['values'][m] = [round(x,2) for x in v]
    return public


def cohort_quantiles(values):
    q = {k:v for k,v in values.items() if k not in ('primary','sensitivity')}
    for label in ('primary','sensitivity'):
        q[label] = {'N':values[label]['N'], 'metric_N':values[label]['metric_N'], 'quantiles':{m:{k:quantile(v,p) for k,p in [('min',0),('p10',.1),('p25',.25),('median',.5),('p75',.75),('p90',.9),('max',1)]} for m,v in values[label]['values'].items()}}
    return q


def wilson(k,n):
    if not n: return {'count': k,'n':n,'share':None,'wilson_95':None}
    z=1.959963984540054; a=k/n; d=1+z*z/n
    mid=(a+z*z/(2*n))/d; half=z*math.sqrt(a*(1-a)/n+z*z/(4*n*n))/d
    return {'count':k,'n':n,'share':a,'wilson_95':[max(0,mid-half),min(1,mid+half)]}


def load_claim_source(source, client):
    if source.startswith(('https://','http://')):
        url=source.rstrip('/')
        if not url.endswith('.json'): url += '/claims/index.json'
        obs,body=client.fetch(url)
        if obs['status'] != 200 or obs.get('error_type'): return None,url
        try: return json.loads(body),url
        except ValueError: return None,url
    path=Path(source)
    if path.is_dir(): path=path/'claims/index.json'
    return read(path),str(path)


def claims(source, client, sample_size=200, seed=20261115, live=False):
    data,source_file=load_claim_source(source,client)
    records=obj(data).get('claims') if isinstance(data,dict) else data
    if not isinstance(records,list) or not all(isinstance(x,dict) for x in records): return {'state':'unknown','source':source_file,'run_id':client.run_id}
    sample=random.Random(seed).sample(records,min(sample_size,len(records)))
    counts=collections.Counter(); topics=collections.Counter(); urls=[]; ids=[]
    for r in records:
        urls.append(r.get('url')); ids.append(r.get('id'))
    for r in sample:
        u=r.get('url',''); parsed=urllib.parse.urlsplit(u)
        stable=parsed.scheme in ('https','http') and bool(parsed.hostname) and bool(parsed.path.strip('/')) and not parsed.query
        counts['stable_url']+=bool(stable)
        counts['citation']+=bool(isinstance(r.get('citation'),str) and r['citation'].strip())
        citation=str(r.get('citation',''))
        mapped=bool(r.get('ssrn') or r.get('ssrn_id') or r.get('doi') or re.search(r'https?://(?:ssrn.com/abstract=|papers.ssrn.com/sol3/papers.cfm\?abstract_id=)\d+|10\.\d{4,9}/\S+',citation))
        counts['identifier_mapped']+=mapped
        counts['content_hash']+=any(bool(re.fullmatch('[0-9a-fA-F]{64}',str(r.get(k,'')))) for k in ('source_sha256','source_pdf_sha256','sha256','content_hash'))
        for topic in r.get('topics',[]): topics[str(topic)]+=1
        if live and stable:
            obs,_=client.fetch(u)
            counts['live_200_ok']+=obs['status']==200 and obs['body_check']=='ok_html_with_title' and not obs.get('error_type')
    return {'state':'observed','run_id':client.run_id,'observed_at':now(),'source_file':source_file,'observed_total':len(records),'declared_total':obj(data).get('count'),'sample_size':len(sample),'seed':seed,'metrics':{k:wilson(counts[k],len(sample)) for k in ('stable_url','citation','identifier_mapped','content_hash')},'live_200_ok':wilson(counts['live_200_ok'],len(sample)) if live else None,'duplicates':{k:sum(n-1 for x,n in collections.Counter(v).items() if x and n>1) for k,v in [('url',urls),('id',ids)]},'sample_topics':dict(topics),'caveats':'Coverage and quality of claim records, not achievement or growth. Stable URL is structural evidence only; resolution is unknown offline. Wilson intervals describe the seeded sample, not extraction correctness. Topic memberships can overlap. Content hashes are presence checks, not verification of source fidelity.'}


def nonnegative(value):
    if type(value) is not int or value < 0: raise ValueError('Expected nonnegative integer count')
    return value


CLAIMS_CAVEATS = 'URL stability is structural; live resolution is unverified. Citation and hash checks establish presence only. Wilson intervals do not verify extraction correctness. See claims_design.md for inventory and design.'


def public_claims(raw, config):
    # Construct output from typed aggregates; never copy source text or paths.
    rid=raw.get('run_id','')
    if not re.fullmatch(r'[A-Za-z0-9_-]+',rid): raise ValueError('Invalid claims run ID')
    if raw.get('state') != 'observed': return {'state':'unknown','run_id':rid}
    allowed={'state','run_id','observed_at','source_file','public_source','observed_total','declared_total','sample_size','seed','metrics','live_200_ok','duplicates','sample_topics','caveats'}
    if set(raw)-allowed: raise ValueError('Unexpected claims source fields')
    total=nonnegative(raw['observed_total']); n=nonnegative(raw['sample_size'])
    if n>total: raise ValueError('Sample exceeds population')
    source=config['claims_public_source']
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@(?:[0-9a-f]{7,40}|[0-9]{4}-[0-9]{2}-[0-9]{2})',source): raise ValueError('Invalid public source identifier')
    stamp=raw['observed_at']; datetime.datetime.fromisoformat(stamp.replace('Z','+00:00'))
    metrics={}
    if set(raw.get('metrics',{})) != {'stable_url','citation','identifier_mapped','content_hash'}: raise ValueError('Incomplete claims metrics')
    for k,v in raw.get('metrics',{}).items():
        if k not in ('stable_url','citation','identifier_mapped','content_hash'): raise ValueError('Unexpected metric')
        count=nonnegative(v['count'])
        if nonnegative(v['n']) != n or count>n: raise ValueError('Invalid sample count')
        metrics[k]=wilson(count,n)
    topics=collections.Counter()
    for k,v in raw.get('sample_topics',{}).items(): topics[k if k in config['claims_topic_codes'] else 'other']+=nonnegative(v)
    out={'state':'observed','run_id':rid,'observed_at':stamp,'public_source':source,'observed_total':total,'sample_size':n,'seed':nonnegative(raw['seed']),'metrics':metrics,'sample_topics':dict(topics),'caveats':CLAIMS_CAVEATS}
    if type(raw.get('declared_total')) is int and raw['declared_total']==total: out['declared_total']=total
    return out


def registry_observation(raw, rid):
    try:
        summary=raw['summary']; keys={'targets':'meaningful_target','listed':'target_listed','pending':'target_pending','not_found':'target_not_found','cannot_verify':'target_cannot_verify'}
        counts={k:nonnegative(summary[v]) for k,v in keys.items()}
        if not counts['targets'] or sum(counts[k] for k in ('listed','pending','not_found','cannot_verify')) != counts['targets']: raise ValueError('Invalid coverage denominator')
        counts['coverage_fraction']=counts['listed']/counts['targets']
        if abs(summary['target_coverage_percent']-100*counts['coverage_fraction'])>.051: raise ValueError('Invalid coverage fraction')
        stamp=raw['generated_at']; datetime.datetime.fromisoformat(stamp.replace('Z','+00:00'))
        definition=raw['target_definition']
        if not isinstance(definition,str) or not definition: raise ValueError('Missing target definition')
        return {'run_id':rid,'state':'observed','observed_at':stamp,'target_definition':definition,'counts':counts}
    except (KeyError,ValueError,TypeError): return {'run_id':rid,'state':'unknown','counts':{}}


def normalized_registry(raw):
    if raw.get('state')!='observed': return {'state':'unknown','counts':{}}
    counts=raw.get('counts',{})
    if 'summary' in counts: return registry_observation(counts,raw.get('run_id','unknown'))
    keys={'meaningful_target':'targets','target_listed':'listed','target_pending':'pending','target_not_found':'not_found','target_cannot_verify':'cannot_verify'}
    try:
        summary={k:counts[v] for k,v in keys.items()}
        fraction=counts['coverage_fraction']
        if type(fraction) not in (int,float) or not 0<=fraction<=1: raise ValueError('Invalid fraction')
        summary['target_coverage_percent']=100*fraction
        return registry_observation({'summary':summary,'generated_at':raw['observed_at'],'target_definition':raw['target_definition']},raw.get('run_id','unknown'))
    except (KeyError,ValueError,TypeError): return {'state':'unknown','counts':{}}


def report(output):
    output=Path(output)
    if (output/'complete.json').exists(): return read(output/'report.json')
    names=('access','readability','indexes','retrieval','compare','claims','registry')
    modules={n:read(output/(n+'.json')) if (output/(n+'.json')).exists() else {'state':'unknown'} for n in names}
    if output.parent.name == 'runs' and any((output/(n+'.json')).exists() and 'run_id' not in modules[n] for n in names): raise ValueError('Missing module run ID')
    if 'claims' in modules and modules['claims'].get('run_id'): modules['claims']=public_claims(modules['claims'],read(ROOT/'config/kaal.json'))
    register=read(output/'exclusion_register.json') if (output/'exclusion_register.json').exists() else {}
    ids={m['run_id'] for m in modules.values() if 'run_id' in m}
    if len(ids)>1 or (ids and register.get('test_run_id') and ids != {register['test_run_id']}): raise ValueError('Mixed run provenance')
    rid=next(iter(ids),register.get('test_run_id','offline-placeholder'))
    r={'version':VERSION,'run_id':rid,'date':register.get('utc_start',now()),'scope':SCOPE,'disclosure':DISCLOSURE,'limitations':LIMITS,'classification_validation':CLASSIFIER,'results':modules,'exclusion_register':register,'request_log_appendix':read(output/'request_log.json') if (output/'request_log.json').exists() else []}
    save(output/'report.json',r)
    paragraphs=[SCOPE,DISCLOSURE,LIMITS,CLASSIFIER]
    if rid=='offline-placeholder': paragraphs.insert(0,'PLACEHOLDER: No live run has occurred.')
    for page in modules['access'].get('pages',[]):
        if urllib.parse.urlsplit(page.get('url','')).hostname=='researchonline.stthomas.edu' and page.get('status')==403:
            paragraphs.append('The request to the recorded St. Thomas profile URL from this network using AEScorecard/0.1 returned HTTP 403, with body classification {}. This observation does not establish treatment of another client.'.format(page.get('body_check','unknown')))
    paragraphs.append('Retrieval records are OpenAlex and Crossref search-index observations, not agent behavior. Crossref topic-query matching is unknown because no owner DOIs are configured. The separate Crossref ORCID-filter count is {}.'.format(obj(obj(modules['indexes'].get('crossref')).get('data')).get('total_results','unknown')))
    metrics=modules['compare'].get('metrics',{})
    if metrics:
        paragraphs.append('OpenAlex comparison: works {}; citations {}; h-index {}; OA works {}; OA works after 2021 {}. Primary benchmark N={}; sensitivity benchmark N={}.'.format(metrics.get('works','unknown'),metrics.get('cited_by','unknown'),metrics.get('h_index','unknown'),metrics.get('oa_works','unknown'),metrics.get('oa_recent','unknown'),obj(obj(modules['compare'].get('comparison')).get('primary')).get('N','unknown'),obj(obj(modules['compare'].get('comparison')).get('sensitivity')).get('N','unknown')))
        paragraphs.append('OA grouped share {} uses denominator {} (OA plus non-OA). OA profile share {} uses denominator {} (profile works). The share discrepancy is {}. Both measures remain separate.'.format(metrics.get('oa_share_grouped','unknown'),metrics.get('oa_denominator_grouped','unknown'),metrics.get('oa_share_profile','unknown'),metrics.get('oa_denominator_profile','unknown'),metrics.get('oa_share_discrepancy','unknown')))
    effect=[]
    exact_path=ROOT/'results/cohort_exact.json'
    if metrics and exact_path.exists():
        exact=read(exact_path); protected=protect_cohort(exact)
        for m in METRICS:
            if type(metrics.get(m)) not in (int,float): continue
            row=[m]
            for label in ('primary','sensitivity'):
                a=1+sum(v>metrics[m] for v in exact[label]['values'][m]); b=1+sum(v>metrics[m] for v in protected[label]['values'][m])
                row.append('{} to {} (difference {:+d})'.format(a,b,b-a))
            effect.append(row)
        paragraphs.append('Public cohort protection is not guaranteed anonymous. Rounded arrays no longer contain the owner exact fractional share values. Exact-match ties may disappear and rounded ties may form; competition positions count strictly greater values.')
    paragraphs.append('This bundle contains no visitor tracking or submission collection; hosting infrastructure may retain request logs.')
    md='# Agent Discoverability Scorecard\n\nRun: '+rid+'\n\n'+'\n\n'.join(paragraphs)+'\n\n'
    content=''.join('<p>'+html.escape(x)+'</p>' for x in ['Run: '+rid]+paragraphs)
    effect_html=table(['Metric','Primary exact to public','Sensitivity exact to public'],effect) if effect else ''
    effect_md='\n\nMetric | Primary exact to public | Sensitivity exact to public\n--- | --- | ---\n'+'\n'.join(' | '.join(row) for row in effect)+'\n' if effect else ''
    content+=effect_html; md+=effect_md
    for label in ('primary','sensitivity'):
        rows=[]
        for m,p in obj(obj(modules['compare'].get('comparison')).get(label)).get('positions',{}).items():
            rows.append([m,str(modules['compare'].get('metrics',{}).get(m,'unknown')),p['text']])
        content+='<section><h2>'+label.title()+' comparison</h2>'+table(['Metric','Value','Position'],rows)+'</section>'
        md+='## '+label.title()+' comparison\n\n'+'\n'.join(' | '.join(x) for x in rows)+'\n\n'
    for name in names:
        module=modules[name]
        rows=[]
        if name=='access': rows=[[x.get('url',''),str(x.get('status')),x.get('body_check','unknown')] for x in module.get('pages',[])]
        elif name=='readability': rows=[[u,k,v] for u,x in module.items() if isinstance(x,dict) for k,v in x.get('items',{}).items()]
        elif name=='retrieval': rows=[[q.get('q',''),str(obj(q.get('openalex')).get('found','unknown')),str(obj(q.get('openalex')).get('matching_ranks',[]))] for q in module.get('queries',[])]
        elif name=='claims': rows=[[k,str(v.get('count')),str(v.get('n')),str(v.get('wilson_95'))] for k,v in module.get('metrics',{}).items()]
        else: rows=[[k,str(v.get('state','unknown') if isinstance(v,dict) else v)] for k,v in module.items() if k not in ('run_id','comparison','metrics')]
        heads={'access':['URL','HTTP status','Body check'],'readability':['URL','Check','State'],'retrieval':['Topic','Found in OpenAlex','Ranks'],'claims':['Coverage','Count','Sample N','Wilson 95% interval']}.get(name,['Item','State'])
        extra = ''
        if name == 'claims':
            extra = '<p>'+html.escape('Observed total: {}; observed at: {}; source: {}; sample size: {}. {}'.format(module.get('observed_total','unknown'),module.get('observed_at','unknown'),module.get('public_source','unknown'),module.get('sample_size','unknown'),module.get('caveats','Coverage and quality unknown in this run.')))+'</p>'
            md += extra.replace('<p>','').replace('</p>','')+'\n\n'
        content+='<section><h2>'+name.title()+'</h2>'+extra+table(heads,rows)+'</section>'
        md+='## '+name.title()+'\n\n'+'\n'.join(' | '.join(x) for x in rows)+'\n\n'
    appendix='<section><h2>Request appendix</h2><p>Full headers, redirect chains, hashes and evidence are retained in <a href="report.json">report.json</a>.</p>'+table(['UTC','URL','Status','Body'],[[x.get('utc',''),x.get('url',''),str(x.get('status')),x.get('body_check','unknown')] for x in r['request_log_appendix']])+'</section>'
    (output/'report.html').write_text(document('Diagnostic report',content+appendix,'report.html','Report'))
    (output/'report.md').write_text(md+'Full evidence and request appendix: [report.json](report.json).\n')
    summary='# Diagnostic summary\n\nRun: '+rid+'\n\n'+'\n\n'.join(paragraphs)+'\n\n[Readable report](report.html), [Markdown report](report.md), [full evidence](report.json).\n'
    (output/'report-summary.md').write_text(summary+effect_md)
    (output/'report-summary.html').write_text(document('Diagnostic summary',''.join('<p>'+html.escape(x)+'</p>' for x in paragraphs)+effect_html+'<p><a href="report.html">Readable report</a> <a href="report.json">Full evidence</a></p>','report-summary.html','Report'))
    return r


def table(heads,rows):
    return '<table><thead><tr>'+''.join('<th scope="col">'+html.escape(str(x))+'</th>' for x in heads)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(x))+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table>'
def series(run):
    def get(n):
        f=run/(n+'.json')
        return read(f) if f.exists() else {}
    access=get('access'); readability=get('readability'); retrieval=get('retrieval'); comparison=get('compare'); claim=get('claims')
    pages=access.get('pages')
    values={'canonical_200_ok':sum(p.get('status')==200 and p.get('body_check')=='ok_html_with_title' and not p.get('error_type') for p in pages) if pages is not None else None,'canonical_403_or_errors':sum((p.get('status') or 0)>=400 or bool(p.get('error_type')) or p.get('status') is None for p in pages) if pages is not None else None}
    checks=[v for x in readability.values() if isinstance(x,dict) for v in x.get('items',{}).values()]
    values['readability_passes']=checks.count('pass') if checks else None
    check_names={k for x in readability.values() if isinstance(x,dict) for k in x.get('items',{})}
    for k in check_names:
        values['readability_pass:'+k]=sum(x.get('items',{}).get(k)=='pass' for x in readability.values() if isinstance(x,dict))
    queries=retrieval.get('queries',[])
    observed=[q for q in queries if obj(q.get('openalex')).get('state')=='observed']
    values['topics_found']=sum(bool(q['openalex'].get('matching_ranks')) for q in observed) if len(observed)==12 else None
    for q in queries:
        o=obj(q.get('openalex')); ranks=o.get('matching_ranks',[])
        values['topic_best_rank:'+q.get('q','')]=min(ranks) if ranks else ('not found in top 25' if o.get('state')=='observed' else None)
    for m in METRICS:
        values[m]=comparison.get('metrics',{}).get(m)
        for label in ('primary','sensitivity'):
            values[label+'_position:'+m]=obj(obj(obj(comparison.get('comparison')).get(label)).get('positions')).get(m,{}).get('position')
    for k,v in claim.get('metrics',{}).items(): values['claims_'+k]=v.get('share')
    values['claims_live_200_ok']=obj(claim.get('live_200_ok')).get('share')
    registry=normalized_registry(get('registry'))
    for k,v in registry.get('counts',{}).items():
        if type(v) in (int,float): values['registry:'+k]=v
    values['registry_known']=1 if registry.get('state')=='observed' else None
    return values


def trend(results, site):
    results=Path(results);site=Path(site);site.mkdir(parents=True,exist_ok=True)
    runs=[]
    for p in (results/'runs').glob('*'):
        if (p/'complete.json').exists() or p.name=='legacy-baseline':
            d=read(p/'report.json') if (p/'report.json').exists() else {}
            runs.append((d.get('date',''),p))
    runs.sort(key=lambda x:(x[0],x[1].name))
    observations=[{'run_id':p.name,'date':date,'metrics':series(p),'registry':normalized_registry(read(p/'registry.json')) if (p/'registry.json').exists() else {'state':'unknown'}} for date,p in runs]
    caveat='Observational diagnostics only; no causal inference. Network, client, index coverage and benchmark versions can change. Single-topic flips and small sample changes are measurement noise candidates. Unknown is not zero. Positions use fixed exact local distributions. Claim coverage uses seeded samples with Wilson intervals, not achievement or verified growth. Registry counts depend on a separately supplied coverage snapshot.'
    data={'observations':observations,'caveats':caveat,'changes':{}}
    module_for=lambda k: ('claims' if k.startswith('claims_') else 'registry' if k.startswith('registry') else 'retrieval' if k.startswith(('topic','topics')) else 'access' if k.startswith('canonical') else 'readability' if k.startswith('readability') else 'compare')
    data['comparisons']={}
    if observations:
        new=observations[-1]; newest=runs[-1][1]
        def definition(path,module):
            f=path/'measurement.json'
            if not f.exists(): return None
            d=read(f).get('modules',{}).get(module)
            if not isinstance(d,dict): return None
            if any(not isinstance(d.get(k),str) or not d[k].strip() for k in ('collector_version','configuration_hash','principal')): return None
            if not re.fullmatch(r'[0-9a-f]{64}',d['configuration_hash']): return None
            for key in ('benchmark_definition','source_definition','sampling_parameters'):
                if not isinstance(d.get(key),dict) or not d[key]: return None
            if not isinstance(d['benchmark_definition'].get('identity'),str) or not d['benchmark_definition']['identity']: return None
            if not isinstance(d['source_definition'].get('identity'),str) or not d['source_definition']['identity']: return None
            sampling=d['sampling_parameters']
            if not isinstance(sampling.get('method'),str) or not sampling['method']: return None
            if type(sampling.get('size')) is not int or sampling['size']<1 or type(sampling.get('seed')) is not int: return None
            return d
        for module in ('access','readability','retrieval','compare','claims','registry'):
            current=definition(newest,module); selected=None; rejected=[]
            relevant=[k for k,v in new['metrics'].items() if module_for(k)==module and v is not None]
            for _,candidate in reversed(runs[:-1]):
                previous=series(candidate)
                if not any(previous.get(k) is not None for k in relevant): continue
                prior=definition(candidate,module)
                if current is not None and current==prior:
                    selected=candidate; break
                rejected.append(candidate.name)
            data['comparisons'][module]={'current_run_id':newest.name,'previous_run_id':selected.name if selected else None,'state':'comparable' if selected else 'not comparable','incompatible_runs':rejected,'reason':None if selected else 'No preceding observation with matching configuration, source, sample parameters and benchmark definitions'}
            previous=series(selected) if selected else {}
            for k,v in new['metrics'].items():
                if module_for(k)!=module: continue
                prev=previous.get(k); delta=v-prev if type(v) in (int,float) and type(prev) in (int,float) else None
                noise='possible noise; significance not assessed'
                if module=='claims' and selected and delta is not None:
                    metric=k[len('claims_'):]
                    ca=read(selected/'claims.json'); cb=read(newest/'claims.json')
                    av=ca.get('metrics',{}).get(metric,ca.get(metric)); bv=cb.get('metrics',{}).get(metric,cb.get(metric))
                    if isinstance(av,dict) and isinstance(bv,dict):
                        ai=wilson(nonnegative(av['count']),nonnegative(av['n']))['wilson_95']; bi=wilson(nonnegative(bv['count']),nonnegative(bv['n']))['wilson_95']
                        if ai and bi: noise='Wilson 95% interval overlap check: '+('overlap' if max(ai[0],bi[0])<=min(ai[1],bi[1]) else 'no overlap')+'; seeded samples, no causal inference'
                data['changes'][k]={'delta':delta,'noise':noise,'current_run_id':newest.name,'previous_run_id':selected.name if selected else None,'classification':'not comparable' if delta is None else ('unchanged' if delta==0 else 'tentative' if k=='topics_found' and abs(delta)==1 else 'observed change')}
    save(results/'trend.json',data);save(site/'trend.json',data)
    content='<p>'+caveat+'</p>';md='# Monthly trend\n\n'+caveat+'\n\n'
    keys=sorted({k for o in observations for k in o['metrics']})
    for k in keys:
        points=[(i,o['metrics'].get(k)) for i,o in enumerate(observations) if type(o['metrics'].get(k)) in (int,float)]
        svg=''
        if points:
            lo=min(v for _,v in points);hi=max(v for _,v in points)
            coords=' '.join('{},{}'.format(5+190*i/max(1,len(observations)-1),35-30*(v-lo)/(hi-lo or 1)) for i,v in points)
            svg='<svg xmlns="http://www.w3.org/2000/svg" width="200" height="40" role="img" aria-label="'+html.escape(k)+' observed values; missing observations omitted"><polyline fill="none" stroke="currentColor" points="'+coords+'"/></svg>'
        rows=[[o['date'],o['run_id'],str(o['metrics'].get(k,'unknown'))] for o in observations]
        content+='<section><h2>'+html.escape(k)+'</h2><p>'+caveat+'</p>'+svg+table(['Date','Run','Value (None means unknown)'],rows)+'<p>'+html.escape(str(data['changes'].get(k,{})))+'</p></section>'
        md+=k+': '+str(data['changes'].get(k,'unknown'))+'\n'
    (site/'trend.html').write_text(document('Monthly diagnostic trend',content,'trend.html'))
    (results/'trend.md').write_text(md)
    latest=observations[-1] if observations else {}
    changes=data['changes']; improved=[];regressed=[]
    for k,d in changes.items():
        delta=d['delta']
        if delta is None or delta==0: continue
        if k in ('canonical_200_ok','readability_passes','topics_found'):
            (improved if delta>0 else regressed).append(k+(' (tentative)' if k=='topics_found' and abs(delta)==1 else ''))
        elif k=='canonical_403_or_errors': (improved if delta<0 else regressed).append(k)
    actions=[]
    if latest:
        path=next(p for _,p in runs if p.name==latest['run_id'])
        a=read(path/'access.json') if (path/'access.json').exists() else {}
        if any(p.get('status')!=200 or p.get('body_check')!='ok_html_with_title' for p in a.get('pages',[])): actions.append('Review failed canonical body and HTTP checks with the hosting administrator.')
        rd=read(path/'readability.json') if (path/'readability.json').exists() else {}
        failures=collections.Counter(k for x in rd.values() if isinstance(x,dict) for k,v in x.get('items',{}).items() if v=='fail')
        actions += ['Repair machine-readability check: '+k+'.' for k,_ in failures.most_common(3)]
        if latest['metrics'].get('topics_found') is None: actions.append('Repeat unknown OpenAlex topic observations from the intended network.')
        if latest['metrics'].get('registry_known') is None: actions.append('Supply the registry coverage snapshot from the separate registry job.')
    while len(actions)<3: actions.append('Review unknown metric states and retain the dated evidence before publication.')
    lines=['Newest run: '+str(latest.get('date','unknown')),'Improved: '+(', '.join(improved) or 'none established'),'Regressed: '+(', '.join(regressed) or 'none established'),'Unknown: '+(', '.join(k for k,v in latest.get('metrics',{}).items() if v is None) or 'no comparable prior observation'),'Small topic changes may be measurement noise; no causation is claimed.']+['Next action '+str(i+1)+': '+a for i,a in enumerate(actions[:3])]
    (results/'monthly_report.md').write_text('\n'.join(lines)+'\n')
    return data


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default=str(ROOT/'config/kaal.json'))
    parser.add_argument('--output',default=str(ROOT/'results'))
    parser.add_argument('--run-id',help='New immutable run directory name')
    subs=parser.add_subparsers(dest='command',required=True)
    for name in ('access','readability','indexes','retrieval','compare','claims','cohort-build','report','all','trend'):
        p=subs.add_parser(name)
        if name=='retrieval':
            g=p.add_mutually_exclusive_group();g.add_argument('--openalex',action='store_true');g.add_argument('--import',dest='import_file')
        if name in ('compare','all'):
            p.add_argument('--cohort',default=str(ROOT/'results/cohort_exact.json'));p.add_argument('--author')
        if name in ('claims','all'):
            p.add_argument('--claims-source',default='https://wulfkaal.github.io/');p.add_argument('--sample-size',type=int,default=200);p.add_argument('--seed',type=int,default=20261115);p.add_argument('--live',action='store_true')
        if name=='cohort-build': p.add_argument('source');p.add_argument('--destination',default=str(ROOT/'site'))
        if name=='report': p.add_argument('--run',required=True)
    args=parser.parse_args()
    if args.command=='trend': parser.error('Publish trends with build_bundle.py and explicit --run and --claims-run selections')
    if args.command=='report': report(Path(args.output)/'runs'/args.run);return
    rid=args.run_id or datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]
    if not re.fullmatch(r'[A-Za-z0-9_-]+',rid): parser.error('Invalid run ID')
    output=Path(args.output)/'runs'/rid
    output.mkdir(parents=True,exist_ok=False)
    if args.command=='cohort-build':
        values,_=cohort(read(args.source)); save(output/'cohort_exact.json',values)
        protected=protect_cohort(values);save(output/'cohort_values.json',protected);save(output/'cohort_quantiles.json',cohort_quantiles(protected));return
    args.output=str(output)
    config=read(args.config);client=Client(output);client.flush()
    save(output/'measurement.json',{'configuration':config,'collector_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'benchmark_sha256':hashlib.sha256(Path(args.cohort).read_bytes()).hexdigest() if hasattr(args,'cohort') and Path(args.cohort).exists() else None,'claims_source':getattr(args,'claims_source',None),'sample_size':getattr(args,'sample_size',None),'seed':getattr(args,'seed',None)})
    for name in (['access','readability','indexes','retrieval','compare','claims'] if args.command=='all' else [args.command]):
        if name=='claims':
            if args.sample_size<1: raise ValueError('Sample size must be positive')
            try: result=claims(args.claims_source,client,args.sample_size,args.seed,args.live)
            except (OSError, ValueError): result={'run_id':rid,'state':'unknown','reason':'Claims source unavailable or invalid'}
            save(output/'claims.json',result)
        else:
            try: run_module(name,args,config,client)
            except (OSError, urllib.error.URLError) as e:
                save(output/(name+'.json'),{'run_id':rid,'state':'unknown','error':type(e).__name__})
    coverage=ROOT/'registries/coverage.json'
    save(output/'registry.json',registry_observation(read(coverage) if coverage.exists() else {},rid))
    measurement=read(output/'measurement.json')
    if (output/'compare.json').exists(): measurement['benchmark_sha256']=read(output/'compare.json').get('benchmark',{}).get('sha256',measurement['benchmark_sha256'])
    principal=getattr(args,'author',None) or config['openalex_author_id']
    measurement['modules']={}
    for module in ('access','readability','indexes','retrieval','compare','claims','registry'):
        measurement['modules'][module]={
            'collector_version':VERSION+':'+measurement['collector_sha256'],
            'configuration_hash':hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest(),
            'principal':principal,
            'benchmark_definition':{'identity':measurement.get('benchmark_sha256') or 'not applicable'},
            'source_definition':{'identity':getattr(args,'claims_source',None) if module=='claims' else json.dumps(config,sort_keys=True)},
            'sampling_parameters':{'method':'seeded' if module=='claims' else 'configured census', 'size':getattr(args,'sample_size',200) if module=='claims' else 1,'seed':getattr(args,'seed',0) if module=='claims' else 0}}
    save(output/'measurement.json',measurement)
    report(output);save(output/'complete.json',{'run_id':rid,'date':now()})
    print(str(output))

if __name__=='__main__': main()
