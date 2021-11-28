#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#define BUF_SIZE 1024

int is_reg_file(char *name) {
    return name != NULL
        && strcmp(name, "-") != 0
        && strcmp(name, "stdin")  != 0
        && strcmp(name, "stdout") != 0
        && strcmp(name, "stderr") != 0;
}


void write_file(char *fin, char *fout)
{
    FILE *in = stdin;
    FILE *out = stdout;
    int in_reg = is_reg_file(fin);

    if(is_reg_file(fin)) {
        in = fopen(fin, "rb");
    }

    int out_reg = is_reg_file(fout);

    if(fout != NULL && strcmp(fout, "stderr") == 0) {
        out = stderr;
    }

    if(out_reg) {
        out = fopen(fout, "wb");
    }

    char buffer[BUF_SIZE];
    size_t size = 0;

    while ((size = fread(buffer, sizeof(*buffer), BUF_SIZE, in)) > 0) {
		fwrite(buffer, sizeof(*buffer), size, out);
	}

    fclose(in);
    fclose(out);
}


int main(int argc, char **argv) {
    if(argc == 1 || strcmp(argv[1], "hello") == 0) {
        puts("Hello world!");
        return 0;
    }
    if(strcmp(argv[1], "exit") == 0) {
        int rc = 0;
        sscanf(argv[2], "%d", &rc);
        return rc;
    }
    if(strcmp(argv[1], "cat") == 0) {
        char *in = argc >= 3 ? argv[2] : NULL;
        char *out = argc >= 4 ? argv[3] : NULL;
        write_file(in, out);
        return 0;
    }
    if(strcmp(argv[1], "echo") == 0) {
        for(int i = 2; i < argc; i++) {
            if(*argv[i] == '\0') continue;
            if(i != 2) putchar(' ');
            printf("%s", argv[i]);
        }
        putchar('\n');
        return 0;
    }

    fprintf(stderr, "Unknown sub-command: %s \n", argv[1]);
    return 100;
}
