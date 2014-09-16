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

static struct peggy_test_s tests[] = {
	{"A1", peggy_parse_A1, valid_rule_A1},
	{"A2", peggy_parse_A2, valid_rule_A2},
	{"A3", peggy_parse_A3, valid_rule_A3},
	{"A4_0", peggy_parse_A4_0, valid_rule_A4},
	{"A4_1", peggy_parse_A4_1, valid_rule_A4},
	{NULL, NULL, NULL}
};

int main(int argc, char *argv[]) {
	size_t i = 0, k = 0;
	char input[3] = {0};

	struct peggy_parser_s parser;
	memset(&parser, 0, sizeof(parser));
	struct peggy_result_s r1, r2;

	while(tests[i].name) {
		k = 0;
		while(product("abcd", 4, input, 3, k)) {
			peggy_parser_init(&parser, input, 3);
			memset(&r1, 0, sizeof(r1));
			tests[i].parse(&parser, 0, &r1, false);
			r2 = tests[i].verif(input, 3);
			if(!equal(r1, r2)) {
				printf("Rule %s failed for input %s, got %d,%lu, wanted %d,%lu\n", tests[i].name, input, r1.v, r1.o, r2.v, r2.o);
			}
			k++;
		}
		i++;
	}
	return 0;
}