#include <stdio.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/mman.h>

int main(int argc, char *argv[]) {
	if(argc != 2) {
		printf("Usage: %s <js>\n", argv[0]);
		return -1;
	}

	int fd = open(argv[1], O_RDONLY);
	if(fd < 0) {
		perror("open");
		return -1;
	}

	struct stat sb;
	if(fstat(fd, &sb) != 0) {
		perror("fstat");
		return -1;
	}

	char *input = mmap(NULL, sb.st_size, PROT_READ, MAP_SHARED, fd, 0);
	if(input == MAP_FAILED) {
		perror("mmap");
		return -1;
	}

	struct peggy_parser_s parser;
	memset(&parser, 0, sizeof(parser));
	struct peggy_result_s result;
	memset(&result, 0, sizeof(result));

	peggy_parser_init(&parser, input, sb.st_size);

	peggy_parse_Program(&parser, 0, &result, true);

	printf("result: %d, %lu\n", result.v, result.o);
	peggy_print_node(result.node, NULL, 0);

	peggy_node_clean(&result.node, true);
	peggy_parser_clean(&parser);

	if(munmap((void *)input, sb.st_size) != 0) {
		perror("munmap");
		return -1;
	}

	return 0;
}