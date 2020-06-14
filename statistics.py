def main():
    fh_html = open('text_heap.html', 'r', encoding='utf8')
    texts = fh_html.read().split('"navbar-nav"')[1:]
    desired_tokens = []
    global text_ids
    text_ids = set()
    for text in texts:
        desired_tokens.extend(process_text(text))

    check_metadata_table()
    create_socio_dict()
    for token in desired_tokens:
        text_id = token['text']
        token["text"] = text_id
        token['speaker'] = socio_by_text_id[text_id]['speaker']
        token['year_of_birth'] = socio_by_text_id[text_id]['year_of_birth']
        token['sex'] = socio_by_text_id[text_id]['sex']
    write_res(desired_tokens)

    get_nums(desired_tokens)
    fh_html.close()


def get_nums(tokens):
    speakers_amount = len(set([token['speaker'] for token in tokens]))
    texts_amount = len(set([token['text'] for token in tokens]))
    #print('спикеров ', speakers_amount)
    #print('текстов ', texts_amount)


def check_metadata_table():
    global table_by_rows, table_by_cols, speakers_col_name_ind
    fh = open('socio.tsv', 'r', encoding='utf8')
    table_by_rows = [row.split('\t') for row in fh.read().split('\n')]
    table_by_cols = tuple(zip(*table_by_rows))
    col_names = table_by_rows[0]

    speakers_col_name = 'Рассказчик (NB: указывать полностью ФИО!)'
    speakers_col_name_ind = col_names.index(speakers_col_name)
    speakers_col = table_by_cols[speakers_col_name_ind][1:]
    years_of_birth_col = table_by_cols[speakers_col_name_ind + 1][1:]
    sexes_col = [row.replace('м', 'm').replace('ж', 'f')
                 for row in table_by_cols[speakers_col_name_ind + 2][1:]]
    socio_cols_by_row = tuple(zip(speakers_col, years_of_birth_col, sexes_col))
    unique_authors = set(speakers_col)
    unique_socio_datapoints = set(socio_cols_by_row)
    assert len(unique_authors) == len(unique_socio_datapoints)
    fh.close()

    col_names = table_by_rows[0]
    col1, col2 = col_names[0], col_names[1]
    text_codes, old_text_names = set(table_by_cols[0][1:]), set(table_by_cols[1][1:])
    assert len(text_codes) == len(old_text_names)


def create_socio_dict():
    global socio_by_text_id
    socio_by_text_id = {}
    sexes_col = [row.replace('м', 'm').replace('ж', 'f')
                 for row in table_by_cols[speakers_col_name_ind + 2]]
    for text_id in text_ids:
        if text_id in table_by_cols[1]:
            row_ind = table_by_cols[1].index(text_id)
            socio_by_text_id[text_id] = dict(speaker = table_by_rows[row_ind][speakers_col_name_ind] or 'NA',
                                             year_of_birth = table_by_rows[row_ind][speakers_col_name_ind+1] or 'NA',
                                             sex = sexes_col[row_ind] or 'NA')
        else:
            if text_id in {'muhammad_shafi_4latin', 'Magomedshapi_Nina_glossed_23_07latin'}:
                socio_by_text_id[text_id] = dict(speaker='Магомед Шафи',
                                                 year_of_birth='1950',
                                                 sex='m')
            elif text_id == 'Polina_text_s_Saadi_TextGridlatin':
                socio_by_text_id[text_id] = dict(speaker='Магомед Шафи',
                                                 year_of_birth='1950',
                                                 sex='m')
            elif text_id == 'kna_2018_17_gljh_1942latin':
                socio_by_text_id[text_id] = dict(speaker='Гюльджахан',
                                                 year_of_birth='1942',
                                                 sex='f')
            elif text_id == '180722_0090':
                socio_by_text_id[text_id] = dict(speaker='Майсарат',
                                                 year_of_birth='1978',
                                                 sex='f')
            elif text_id == '180724_0081_18-10-18':
                socio_by_text_id[text_id] = dict(speaker='Назиле',
                                                 year_of_birth='1963',
                                                 sex='f')
            elif text_id == '180722_0171':
                socio_by_text_id[text_id] = dict(speaker='180722_0171',
                                             year_of_birth='NA',
                                             sex='NA')
            else:
                socio_by_text_id[text_id] = dict(speaker=text_id,
                                                 year_of_birth='NA',
                                                 sex='NA')


def process_text(text):
    examples = text.split('<table class="example">')[1:]
    desired_tokens = []
    for example in examples:
        desired_tokens.extend(process_example(example))
    global text_ids
    for token in desired_tokens:
        text_id = get_text_id(text)
        text_ids.add(text_id)
        token['text'] = text_id
    return desired_tokens


def get_text_id(text):
    text_id_beginning = text.index('<h2><b>') + 7
    text_id_ending = text.index('</b>', text_id_beginning)
    text_id = text[text_id_beginning:text_id_ending]
    return text_id.strip()


def process_example(example):
    rows = example.split('<tr')[1:]
    assert len(rows) % 2 == 0

    glosses = False
    tokens = []
    for row in rows:
        for_tokens = row.split('</td><td>')
        if not glosses:
            words_amount = len(for_tokens)
            wordforms = for_tokens
        else:
            assert len(for_tokens) == words_amount
            tokens.extend(zip(wordforms, for_tokens))
        glosses = not glosses
    return filter_tokens(tokens)


def get_example_num(example):
    try:
        button_beg = example.index('<button')
        button_end = example.find('">', button_beg)
        next_tag_beg = example.find('<', button_end)
        example_num = example[button_end + 2:next_tag_beg]
        # print(button_beg, button_end, next_tag_beg)
        return example_num
    except ValueError:
        print(example)
        return '1'


def filter_tokens(tokens):
    desired_tokens = []
    for token in tokens:
        com_beg = token[1].find('COM ')
        add_beg = token[1].find('ADD')
        button_beg = token[0].find('<button')
        if (button_beg != -1):
            continue
        if ((com_beg == -1) and (add_beg == -1)):
            continue
        token = process_token(token)
        if token:
            desired_tokens.append(token)
    return desired_tokens


def process_token(token):
    res = {}
    morphemes = token[0].split('   ')[0]\
        .strip('.,?')\
        .replace('=', '-').replace('&lt;', '-').replace('&gt;', '-').replace('><td>', '')\
        .split('-')
    if not marker_found(res, morphemes[-1]):
        return {}

    base = '-'.join(morphemes[:-1]) + res['epenth']
    res['base'] = base
    phon(res, base)

    glosses = token[1].split('   ')[0]\
        .replace('=', '-').replace('&lt;', '-').replace('&gt;', '-').replace('><td>', '')\
        .split('-')
    try:
        if 'OBL' in glosses[-2]:
            res['obl'] = morphemes[-2] + res['epenth']
        else:
            res['obl'] = res['epenth']
    except IndexError:
        res['obl'] = res['epenth']
    return res


def marker_found2(res, ending):
    class otherMarker(Exception): pass
    class otherK(otherMarker): pass
    class otherX(otherMarker): pass

    try:
        k_pos = ending.find('k')
        x_pos = ending.find('x')
        if not ((k_pos != -1) ^ (x_pos != -1)):
            raise otherMarker()
        if k_pos:
            if ending[-2::-1] == 'an':
                raise otherK()
            if k_pos == -3:
                if ending[-2] in 'wʷ':
                    raise otherK()
                res['marker_labialized'] = 1
            elif k_pos == -2:
                res['marker_labialized'] = 0
            else:
                raise otherK()
            res['gramm'] = 'com'
        elif x_pos:
            if ending[-1] == 'a':
                raise otherX()
            if k_pos == -3:
                if ending[-2:] in 'wʷ':
                    raise otherX()
                res['marker_labialized'] = 1
            elif k_pos == -2:
                res['marker_labialized'] = 0
            else:
                raise otherX()
            res['gramm'] = 'add'
        res['obl'] = ending[:max(k_pos, x_pos)]
        return True
    except (otherX, otherK) as err:
        print(err)
        return False


def marker_found(res, ending):
    k_pos = ending.find('k')
    x_pos = ending.find('x')
    if not ((k_pos != -1) ^ (x_pos != -1)):
        return False
    if k_pos != -1:
        if ending[-2:] != 'an':
            return False
        if len(ending) - k_pos == 4:
            res['marker_labialised'] = 1
        elif len(ending) - k_pos == 3:
            res['marker_labialised'] = 0
        else:
            return False
        res['gramm'] = 'com'
    elif x_pos != -1:
        if ending[-1] != 'a':
            return False
        if (len(ending) - x_pos) == 3:
            res['marker_labialised'] = 1
        elif (len(ending) - x_pos) == 2:
            res['marker_labialised'] = 0
        else:
            return False
        res['gramm'] = 'add'
    res['ending'] = ending
    res['epenth'] = ending[:max(k_pos, x_pos)]
    return True


def phon(res, base):
    res['bilabial_stop'] = 1 if (('b' in base) or ('p' in base)) else 0
    res['nasal'] = 1 if ('m' in base) else 0
    res['labialised'] = 1 if ('ʷ' in base) else 0
    res['fricative'] = 1 if ('v' in base) else 0
    look_on_w(res, base)
    res['vowel'] = 1 if (('u' in base) or ('ü' in base) or ('o' in base)) else 0


def look_on_w(res, base):
    for morph in base.split('-'):
        assert morph.count('w') <= 1
        w_pos = morph.find('w')
        if w_pos == -1:
            continue
        elif w_pos == 0:
            res['fricative'] = 1
        else:
            if morph[w_pos - 1] in {'k', 'x', 'ˁ', 'ʁ', 'g', 'ɢ', "'", 'q'}:
                res['labialised'] = 1
            else:
                res['fricative'] = 1


def write_res(tokens):
    fh = open('data_statistics.txt', 'w', encoding='utf8')
    col_names = ('gramm', 'marker_labialised', 'obl',
                 'bilabial_stop', 'nasal', 'labialised', 'fricative', 'vowel',
                 'speaker', 'year_of_birth', 'sex')
    data_rows = []
    for token in tokens:
        values = []
        for prop in col_names:
            values.append(str(token[prop]))
        data_rows.append('\t'.join(values))
    fh.write('\n'.join(['\t'.join(col_names)] + data_rows))
    fh.close()

main()