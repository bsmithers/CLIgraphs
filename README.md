CLIgraphs
=========

Easy generation of Python/Matplotlib graphs from the command line.

## Examples

A simple scatter plot of length vs width:
```
scatter.py examples/iris.tsv --x-label 'Sepal length' --y-label 'Sepal width'
```

Multiple datasets (psst, named pipes just work too):
```
scatter.py <(grep 'setosa' examples/iris.tsv) \
<(grep 'versicolor' examples/iris.tsv) \
<(grep 'virginica' examples/iris.tsv) \
--legend 'Setosa,Versicolor,Virginica' \
--point-size 60,25,25 \
--alpha 0.8
```
