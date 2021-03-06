import nltk
from relation import Relation

def build_sentence_tree_parent(tagged_sentence):
    """Builds the sentence tree based on the IOB tags for person and date"""
    phrase=[]
    label = ""
    token_list = []
    for token in tagged_sentence:
        iob = token[2]
        word = token[:-1]
        if(iob=='O'):
            if(phrase!=[]):
                token_list.append(nltk.Tree(label,phrase))
                label=""
                phrase=[]
                token_list.append(word)
            else:
                token_list.append(word)
        else:
            if(iob[2:] in ["PERSON","DATE"]):
                if(label==iob[2:] or label==""):
                    label = iob[2:]
                    phrase.append(word)
                else:
                    token_list.append(nltk.Tree(label, phrase))
                    label = ""
                    phrase = []
                    phrase.append(word)

    if (phrase != []):
        token_list.append(nltk.Tree(label, phrase))

    return token_list

def build_sentence_tree(tagged_sentence):
    """Builds the sentence tree based on the IOB tags for person and date"""
    phrase=[]
    label = ""
    token_list = []
    for token in tagged_sentence:
        iob = token[2]
        word = token[:-1]
        if(iob=='O'):
            if(phrase!=[]):
                token_list.append(nltk.Tree(label,phrase))
                label=""
                phrase=[]
                token_list.append(word)
            else:
                token_list.append(word)
        else:
            if(label==iob[2:] or label==""):
                label = iob[2:]
                phrase.append(word)
            else:
                token_list.append(nltk.Tree(label, phrase))
                label = ""
                phrase = []
                phrase.append(word)

    if (phrase != []):
        token_list.append(nltk.Tree(label, phrase))

    return token_list

def getLeaves(tree):
    entity=[]
    for leave in tree.leaves():
        entity.append(leave)
    return entity

def extract_date_relations(sentence):
    birthdate = r"""
      BORN:
        {<VBD>?<VBN><IN|PERSON|CC>*}          # Chunk everything
      BIRTHDATE:
        {<PERSON><.|..|...|-.RB->*<BORN><.|..|...|-.RB-|BORN|PRP.>*<DATE>}          # here
        {<DATE><.|..|...>*<PERSON><.|..|...>*<BORN>}
        {<BORN><DATE>*<.|..|...|DATE>*<PERSON>}
      """
    results = []
    predicate = "DateOfBirth"

    annotation = sentence["annotation"]
    text = sentence["text"]
    tagged_sentence = [(x[1], x[3], x[4]) for x in annotation]

    token_list = build_sentence_tree_parent(tagged_sentence)
    cp = nltk.RegexpParser(birthdate, loop=2)
    # print(text)
    BIRTH_DATE_RELATION = cp.parse(token_list)
    # print(BIRTH_DATE_RELATION)
    # TREE = cp.parse(token_list)
    # #TREE.draw()
    # birth = nltk.RegexpParser(birthdate)
    # print(birth.parse(TREE))
    for subtree in BIRTH_DATE_RELATION.subtrees(filter=lambda t: t.label() == 'BIRTHDATE'):
        relation_dict = {}
        for nestedtree in subtree.subtrees(filter=lambda t: t.label() in ['PERSON', 'DATE']):
            if (nestedtree.label() == 'PERSON' and "PERSON" not in relation_dict):
                relation_dict["PERSON"] = [x[0] for x in getLeaves(nestedtree)]
            if (nestedtree.label() == 'DATE'):
                relation_dict["DATE"] = [x[0] for x in getLeaves(nestedtree)]
        if ("PERSON" in relation_dict and "DATE" in relation_dict):
            person = " ".join(relation_dict["PERSON"])
            date = " ".join(relation_dict["DATE"])
            rel = Relation(person, predicate, date)
            results.append(rel)
    return results

def extract_parent_relations(sentence):
    parents = r"""
                      BORN:
                         {<VBD>?<VBN><IN|PERSON|CC>*}
                      ADDNINFO:
                		{<-LRB-><.|..|PERSON|DATE|BORN|PARENTS>*<-RRB->}
                      PARENTS:
                        {<IN><.|..|...|DATE|HYPH>*<PERSON><.|..|...|DATE|ADDNINFO|HYPH>*<CC><.|..|...|DATE|BORN|PRP.>*<PERSON>}
                		{<BORN><IN><PERSON>}
                		{<BORN>*<PERSON><CC><PERSON>}
                		{<DT|NN|IN|DATE>+<PERSON><CC>*<PERSON>*}
                      RELATION:
                        {<BORN>*<.|..|...|DATE|ADDNINFO|PRP.>*<PERSON><BORN>*<.|..|...|DATE|ADDNINFO|BORN|PRP.>*<PARENTS>}
                      """
    results = []
    predicate = "HasParent"

    annotation = sentence["annotation"]
    text = sentence["text"]
    tagged_sentence = [(x[1], x[3], x[4]) for x in annotation]

    token_list = build_sentence_tree_parent(tagged_sentence)
    cp = nltk.RegexpParser(parents,loop=3)
    #print(text)
    PARENT_RELATION = cp.parse(token_list)
    # print(PARENT_RELATION)
    # print("Person List")
    relation_list = []
    for subtree in PARENT_RELATION.subtrees(filter=lambda t: t.label() == 'RELATION'):
        subject = []
        parent_names = []
        ts = ()
        for info in subtree:
            if (type(info) != type(ts) and info.label() == 'PERSON'):
                subject.extend([x[0] for x in info.leaves()])
        for parents_rel in subtree.subtrees(filter=lambda t: t.label() == 'PARENTS'):
            for node in parents_rel:
                if(type(node)!= type(ts) and node.label()=='PERSON'):
                    parent_names.append(" ".join([x[0] for x in node.leaves()]))
        #print(subject)
        #print(parent_names)
        for name in parent_names:
            rel = Relation(" ".join(subject), predicate, name)
            relation_list.append(rel)
    return relation_list