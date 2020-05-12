import math
import sys
import itertools

# used to display / pprint cky matrix
class Chart:
    def __init__(self, dim_x=3, dim_y=3):
        self.chart = [['N/A']*dim_x]*dim_y
        self.spacing = 15

    def set(self, x, y, val):
        self.expand(x+1,y+1)
        self.chart[y][x] = val

    def expand(self, dim_x, dim_y):
        chart2 = []
        for row in self.chart:
            line = []
            for elem in row:
                line.append(elem)
            for i in range(dim_x - len(row)):
                line.append('N/A')
            chart2.append(line)
        if len(chart2) == 0:
            chart2 = self.chart
        for i in range(dim_y - len(self.chart)):
            chart2.append(['N/A']*len(chart2[0]))
        self.chart = chart2

    def pprint(self):
        for i in range(len(self.chart)):
            line_str = ""
            for j in range(len(self.chart[0])):
                if self.chart[i][j] == 'N/A':
                    line_str += '[' + ' '*self.spacing + ']'
                else:
                    line_str += '[' + repr(self.chart[i][j]) + ' '*(self.spacing-len(repr(self.chart[i][j]))) + ']'
            print(line_str) 

    def get_last(self):
        lst = []
        for line in self.chart:
            for elem in line[::-1]:
                if elem != 'N/A':
                    lst.append(elem)
                    break
        return lst

    def matrix(self, matrix):
        matr = []
        for line in matrix:
            ln = []
            for elem in line:
                if elem == 'N/A':
                    ln.append(elem)
                else:
                    ln.append(' '.join(set([i.tag for i in elem])))
            matr.append(ln)
        self.chart = matr

# represents rules
class Rule:
    def __init__(self, input_elem, out_list, penalty):
        self.input = input_elem
        self.output = out_list
        self.penalty = penalty

class Node:
    def __init__(self, tag, loc=None, left=None, right=None, penalty=0):
        self.tag = tag
        self.loc = loc
        self.left = left
        self.right = right
        self.penalty = penalty

    def __repr__(self):
        if self.left == None and self.right == None:
            return self.tag
        elif self.right == None:
            return "( {} {} )<{}>".format(self.tag, self.left, self.penalty)
        else:
            return "( {} {} {} )<{}>".format(self.tag, self.left, self.right, self.penalty)
         
# represents grammar
class Grammar:
    def __init__(self, rules, right_hand_dict):
        self.rules = rules
        self.right_hand = right_hand_dict

    def get_last(self, matrix):
        lst = []
        for line in matrix:
            for elem in line[::-1]:
                if elem != 'N/A':
                    lst.append(elem)
                    break
        return lst

    def gen_nodes(self, left_node, down_node, loc):
        nodes = []
        l_tag = left_node.tag
        d_tag = down_node.tag
        for tag in self.get_tags([l_tag, d_tag]):
            nodes.append(Node(tag=tag.input,loc=loc,left=left_node,right=down_node,penalty=tag.penalty))
        return nodes

    def get_tags(self, elem):
        if repr(elem) not in self.right_hand:
            return []
        return [i for i in self.right_hand[repr(elem)]]    
 
    def cky(self, sentences):
        charts = []
        for sentence in sentences:
            opt_matrix = [['N/A' for i in range(1+len(sentence))] for j in range(len(sentence))]
            
            # words
            for i,elem in enumerate(sentence):
                opt_matrix[i][i] = [Node(str(elem), loc=(i,i), penalty=0.0)]

            # tags
            next_elem = [[i+1,i] for i in range(len(sentence))]
            for pair in next_elem:
                lst = []
                for last in opt_matrix[pair[1]][pair[0]-1]:
                    for elem in self.right_hand[repr([last.tag])]:
                        lst.append(Node(tag=elem.input, left=opt_matrix[pair[1]][pair[0]-1], loc=pair, penalty=elem.penalty))
                if len(lst) == 0:
                    lst = 'N/A'
                opt_matrix[pair[1]][pair[0]] = lst
            
            # spans
            while len(next_elem) > 0:
                next_elem = [[pair[0]+1,pair[1]] for pair in next_elem][:-1]
                for pair in next_elem:
                    lst = []
                    for left in opt_matrix[pair[1]][:pair[0]]:
                        for d in opt_matrix[pair[1]:]:
                            down = d[pair[0]]
                            if left !='N/A' and down != 'N/A':
                                for left_i in left:
                                    for down_i in down:
                                        for n in self.gen_nodes(left_i, down_i, pair):
                                            lst.append(n)
                    if len(lst) == 0:
                        lst = 'N/A'
                    opt_matrix[pair[1]][pair[0]] = lst 
            print("PARSING::\t{}".format(' '.join(sentence)))
            
            valids = self.get_valid_trees(opt_matrix,sentence)
            print(len(valids))
            if not valids:
                print("No Parse!")
            else:
                for n,elem, in enumerate(sorted(valids, key=lambda x: x[1])):
                    print("Tree {} weight:\t{}".format(n+1, round(elem[1],2)))
                    print("Tree {} parse:".format(n+1))
                    print(elem[0])
            print()

    def get_valid_trees(self, opt_matrix, sentence):
        lst = []
        x = [i.tag for i in opt_matrix[0][-1] if opt_matrix[0][-1]!='N/A']
        if 'ROOT' not in x:
            return False
        else:
            for root in opt_matrix[0][-1]:
                save = repr(root)
                for elem in sentence:
                    if save.count('['+elem+']') != sentence.count(elem):
                        break
                else:
                    if save.count('(') == save.count(')'):
                        penalty = 0
                        save = ''.join([i for i in save if i not in ['[',']']])
                        while '<' in save:
                            penalty_txt = save.split('<')[1].split('>')[0]
                            save = save.replace('<'+penalty_txt+'>',"",1)
                            penalty += float(penalty_txt)
                        lst.append([save, penalty])
            return lst 

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print('incorrect # of arguments')
    else:
        grammar_file = sys.argv[1]
        sentence_file = sys.argv[2]
        
        rules = []
        right_hand = {}

        with open(grammar_file) as g:
            for line in g:
                lst = line.rstrip().split(' ')
                if len(lst) > 1:
                    if float(lst[0]) == 0.0:
                        rules.append(Rule(lst[1],lst[2:],0))
                    else:
                        rules.append(Rule(lst[1],lst[2:],float(lst[0])))
                    
                    if repr(lst[2:]) in right_hand:
                        right_hand[repr(lst[2:])] = right_hand[repr(lst[2:])] + [rules[-1]]
                    else:
                        right_hand[repr(lst[2:])] = [rules[-1]]
                
        grammar = Grammar(rules, right_hand)
        
        with open(sentence_file) as s:
            sentences = [i.rstrip().split(' ') for i in s]
        
        grammar.cky(sentences)
 

