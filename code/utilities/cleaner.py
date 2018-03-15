def quote_cleaner( input_filename, output_filename ):
    inside_tag = False
    input_file = open(input_filename, 'r')
    output_file = open(output_filename, 'w')
    for line in input_file:
        new_line = ''
        for char in line:
            if char == '<':
                inside_tag = True
            if char == '>':
                inside_tag = False
            if char == '"' and not inside_tag:
                continue
            new_line += char
        output_file.write(new_line)
    input_file.close()
    output_file.close()