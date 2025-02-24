export function search(data, keys, text) {
    var obj = [];
    if (data) {
      for (var i = 0; i < data.length; i++) {
        for (var j = 0; j < keys.length; j++) {
          if (data[i][keys[j]]) {
            if (
              data[i][keys[j]]
                .toString()
                .toLowerCase()
                .indexOf(text.toString().toLowerCase()) !== -1
            ) {
              obj.push(data[i]);
              break;
            }
          }
        }
      }
    }
    return obj;
  }
