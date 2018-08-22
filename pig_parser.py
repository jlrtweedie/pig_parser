import sys
import numpy as np
import numpy.ma as ma
from functools import reduce

# Local variable storage - values are stored in numpy arrays for
# ease of manipulation, using np masks for the filter function
VARIABLES = dict()

def _load(varname, filename):
    """Loads .csv into numpy array"""
    VARIABLES[varname] = np.genfromtxt(filename, delimiter=',', dtype=np.int32)

def _dump(varname):
    """Dumps array to console with .csv formatting"""
    # Catch exception for arrays masked to a single row
    if len(VARIABLES[varname].shape) == 1:
        print(','.join(map(str, VARIABLES[varname])))
    # Otherwise iterates rowwise
    else:
        for row in VARIABLES[varname]:
            print(','.join(map(str, row)))

def _filter(varname1, varname2, column, value, operator):
    """Generates a numpy mask, masks input array, returns compressed
        output to variables dict"""
    # To do: generate masks programatically given operator input
    # Operators are reversed in mask because true values are masked, not false
    if operator == '==':
        mask = np.repeat(VARIABLES[varname1][:,column]==value,
                         VARIABLES[varname1].shape[1])
    elif operator == '>':
        mask = np.repeat(VARIABLES[varname1][:,column]<=value,
                         VARIABLES[varname1].shape[1])
    elif operator == '>=':
        mask = np.repeat(VARIABLES[varname1][:,column]<value,
                         VARIABLES[varname1].shape[1])
    elif operator == '<':
        mask = np.repeat(VARIABLES[varname1][:,column]>=value,
                         VARIABLES[varname1].shape[1])
    elif operator == '<=':
        mask = np.repeat(VARIABLES[varname1][:,column]>value,
                         VARIABLES[varname1].shape[1])

    VARIABLES[varname2] = ma.compress_rows(ma.array(VARIABLES[varname1],
                                           mask=mask))

def _generate(varname1, varname2, commands):
    """Generates a new array given a series of command inputs"""
    # Testing with only addition and multiplication initially but this can
    # be expanded easily once the command input is well parsed
    columns = []
    for command in commands:
        if isinstance(command, int):
            columns.append(VARIABLES[varname1][:,command])
        elif isinstance(command, list):
            if command[1] == '+':
                columns.append(VARIABLES[varname1][:,command[0]] + command[2])
            elif command[1] == '*':
                columns.append(VARIABLES[varname1][:,command[0]] * command[2])

    VARIABLES[varname2] = reduce(lambda x, y: np.column_stack((x, y)), columns)

def check_var(varname):
    """"Checks if varname exists in variables dict"""
    if VARIABLES.get(varname) is not None:
        return True
    else:
        return False

def pig_parser(line):
    """Parses string inputs and calls appropriate function"""
    # Checks for blank newlines
    if line == '':
        return
    else:
        elements = line.split()

    # Dump function - ensures variable to be dumped has been assigned previously
    if elements[0].lower() == 'dump':
        varname = elements[1]

        if check_var(varname):
            _dump(varname)
        else:
            raise KeyError('Variable {} is undefined'.format(varname))

    # Load function - checks if variable was previously assigned and prevents
    # overwrite (as do filter and generate) but this can be removed
    elif elements[2].lower() == 'load':
        varname = elements[0]
        filename = elements[3]

        if not check_var(varname):
            _load(varname, filename)
        else:
            raise KeyError('Variable {} was previously assigned'.format(varname))

    # Filter function
    elif elements[2].lower() == 'filter':
        varname1 = elements[3]
        varname2 = elements[0]
        column = int(elements[5].replace('$', ''))
        value = int(elements[7])
        operator = elements[6]

        if check_var(varname1) and not check_var(varname2):
            _filter(varname1, varname2, column, value, operator)
        elif not check_var(varname1):
            raise KeyError('Variable {} is undefined'.format(varname1))
        elif check_var(varname2):
            raise KeyError('Variable {} was previously assigned'.format(varname2))

    # Generate function - combines and reparses generator commands from elements
    # and passes a well structured list to the generate function to perform
    # arithmetic operations
    elif elements[2].lower() == 'foreach':
        varname1 = elements[3]
        varname2 = elements[0]
        commands = ' '.join(elements[5:]).replace('$', '').split(', ')
        for i, command in enumerate(commands):
            try:
                commands[i] = int(command)
            except ValueError:
                commands[i] = command.split(' ')
                commands[i][0], commands[i][2] = int(commands[i][0]), int(commands[i][2])
        if check_var(varname1) and not check_var(varname2):
            _generate(varname1, varname2, commands)
        elif not check_var(varname1):
            raise KeyError('Variable {} is undefined'.format(varname1))
        elif check_var(varname2):
            raise KeyError('Variable {} was previously assigned'.format(varname2))


###############################################################################


if __name__ == '__main__':

    # Load pig scripts from console
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as script:
            for line in script:
                pig_parser(line)

    while True:
        line = input('> ')
        pig_parser(line)
