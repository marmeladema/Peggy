#include <stdio.h>

char *product(char *set, size_t len, char *res, size_t times, size_t index) {
	if(!set || len == 0 || !res || times == 0) {
		return NULL;
	}
	res[0] = set[index%len];

	size_t i, t = index;
	for(i = 1; i < times; i++) {
		t = t/len;
		res[i] = set[t%len];
	}
	if(t >= len) {
		return NULL;
	}
	return res;
}

bool equal(struct peggy_result_s r1, struct peggy_result_s r2) {
	return (r1.v == r2.v && r1.o == r2.o);
}

typedef bool (*peggy_parse_fun_t)(struct peggy_parser_s *p, size_t i, struct peggy_result_s *result, bool ast);
typedef struct peggy_result_s (*peggy_verif_fun_t)(const char *i, size_t len);

struct peggy_test_s {
	const char *name;
	peggy_parse_fun_t parse;
	peggy_verif_fun_t verif;
};

struct peggy_result_s valid_patterns(const char *i, size_t len, char *patterns[]) {
	struct peggy_result_s r;
	memset(&r, 0, sizeof(r));
	while(*patterns) {
		if(strncmp(i, *patterns, strlen(*patterns)) == 0) {
			r.v = true;
			r.o = strlen(*patterns);
			return r;
		}
		patterns++;
	}
	return r;
}

/* A1 <= 'a' */
struct peggy_result_s valid_rule_A1(const char *i, size_t len) {
	struct peggy_result_s r;
	memset(&r, 0, sizeof(r));
	if(len > 0 && i[0] == 'a') {
		r.v = true;
		r.o = 1;
	}
	return r;
}

/* A1 <= 'a'? */
struct peggy_result_s valid_rule_A2(const char *i, size_t len) {
	struct peggy_result_s r;
	memset(&r, 0, sizeof(r));
	r.v = true;
	if(len > 0 && i[0] == 'a') {
		r.o = 1;
	}
	return r;
}

/* A1 <= 'a'* */
struct peggy_result_s valid_rule_A3(const char *i, size_t len) {
	struct peggy_result_s r;
	memset(&r, 0, sizeof(r));
	r.v = true;
	while(r.o < len && i[r.o] == 'a') {
		r.o += 1;
	}
	return r;
}

/* #A1 <= 'a'+ */
struct peggy_result_s valid_rule_A4(const char *i, size_t len) {
	struct peggy_result_s r = valid_rule_A3(i, len);
	if(r.v && r.o == 0) {
		r.v = false;
	}
	return r;
}

struct peggy_result_s valid_rule_A5(const char *i, size_t len) {
	struct peggy_result_s r;
	memset(&r, 0, sizeof(r));
	while(r.o < len && (i[r.o] == 'a' || i[r.o] ==  'b')) {
		r.o += 1;
	}
	if(r.o > 0) {
		r.v = true;
	}
	return r;
}

struct peggy_result_s valid_rule_A6(const char *i, size_t len) {
	char *patterns[] = {
		"ab", "acd", NULL
	};
	return valid_patterns(i, len, patterns);
}

struct peggy_result_s valid_rule_A7(const char *i, size_t len) {
	char *patterns[] = {
		"a", "bc", "bd", NULL
	};
	return valid_patterns(i, len, patterns);
}

struct peggy_result_s valid_rule_A8(const char *i, size_t len) {
	char *patterns[] = {
		"abc", NULL
	};
	return valid_patterns(i, len, patterns);
}

struct peggy_result_s valid_rule_A9(const char *i, size_t len) {
	char *patterns[] = {
		"a", "b", "c", NULL
	};
	return valid_patterns(i, len, patterns);
}

static struct peggy_test_s tests[] = {
	{"A1", peggy_parse_A1, valid_rule_A1},
	{"A2", peggy_parse_A2, valid_rule_A2},
	{"A3", peggy_parse_A3, valid_rule_A3},
	{"A4_0", peggy_parse_A4_0, valid_rule_A4},
	{"A4_1", peggy_parse_A4_1, valid_rule_A4},
	{"A5_0", peggy_parse_A5_0, valid_rule_A5},
	{"A5_1", peggy_parse_A5_1, valid_rule_A5},
	{"A5_2", peggy_parse_A5_2, valid_rule_A5},
	{"A6", peggy_parse_A6, valid_rule_A6},
	{"A7", peggy_parse_A7, valid_rule_A7},
	{"A8_0", peggy_parse_A8_0, valid_rule_A8},
	{"A8_1", peggy_parse_A8_1, valid_rule_A8},
	{"A9_0", peggy_parse_A9_0, valid_rule_A9},
	{"A9_1", peggy_parse_A9_1, valid_rule_A9},
	{NULL, NULL, NULL}
};

int main(int argc, char *argv[]) {
	size_t i = 0, k = 0;
	char input[4] = {0, 0, 0, 0};

	struct peggy_parser_s parser;
	memset(&parser, 0, sizeof(parser));
	struct peggy_result_s r1, r2;

	while(tests[i].name) {
		k = 0;
		while(product("abcd", 4, input, 3, k)) {
			//printf("Matching %s against input %c%c%c\n", tests[i].name, input[0], input[1], input[2]);
			peggy_parser_init(&parser, input, strlen(input));
			memset(&r1, 0, sizeof(r1));
			tests[i].parse(&parser, 0, &r1, true);
			r2 = tests[i].verif(input, 3);
			if(!equal(r1, r2)) {
				printf("Rule %s failed for input %s, got %d,%lu, wanted %d,%lu\n", tests[i].name, input, r1.v, r1.o, r2.v, r2.o);
			}
			// peggy_print_node(r1.node, NULL, 0);
			peggy_node_clean(&r1.node);
			peggy_parser_clean(&parser);
			k++;
		}
		i++;
	}
	return 0;
}